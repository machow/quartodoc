"""The interlinks module fully specifies the behavior of an interlinks filter.

Note that this module largely exists for two reasons:

* Allow people to explore / debug interlinks in python.
* Provide a reference implementation for the lua interlinks filter.

See quartodoc.tests.test_interlinks for its implementation, and the fully
loaded specification.
"""

from __future__ import annotations

import os
import itertools
import json
import requests
import sphobjinv
import warnings
import yaml

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Annotated, Union, Optional

from ._pydantic_compat import BaseModel, Field


ENV_PROJECT_ROOT: str = "QUARTO_PROJECT_ROOT"

# Errors -----------------------------------------------------------------------


class RefSyntaxError(Exception):
    """An error parsing an interlinks reference."""


class InvLookupError(Exception):
    """An error looking up an entry from inventory files."""


# Save inventories from url ---------------------------------------------------
# Note that this is the one piece used by quartodoc (whereas everything else
# in this module is a model of the lua filter behavior).


def inventory_from_url(url: str) -> sphobjinv.Inventory:
    """Return an inventory file by fetching from a url.

    Use the prefix file:// to load the file from disk.
    """

    if url.startswith("file://"):
        with open(url.replace("file://", "", 1), "rb") as f:
            raw_content = f.read()
    else:
        r = requests.get(url)
        r.raise_for_status()
        raw_content = r.content

    if url.endswith(".inv"):
        inv = sphobjinv.Inventory(zlib=raw_content)
    elif url.endswith(".txt"):
        inv = sphobjinv.Inventory(plaintext=raw_content)
    else:
        raise NotImplementedError("Inventories must be .txt or .inv files.")

    return inv


# Utility functions -----------------------------------------------------------


def get_path_to_root():
    # In lua filters you can use quarto.project.offset
    return Path(os.environ[ENV_PROJECT_ROOT])


def parse_rst_style_ref(full_text: str):
    """
    Returns
    -------
    tuple
        The parsed title (None if no title specified), and corresponding reference.
    """

    import re

    m = re.match(r"(?P<text>.+?)\<(?P<ref>[a-zA-Z\.\-: _]+)\>", full_text)
    if m is None:
        # TODO: print a warning or something
        return full_text, None

    text, ref = m.groups()

    return ref, text


def parse_md_style_link(full_text: str):
    import re

    m = re.match(r"\[(?P<text>.*?)\]\((?P<ref>.*?)\)", full_text)

    if m is None:
        raise Exception()

    text, ref = m.groups()

    return ref, text


# Dataclasses representing pandoc elements ------------------------------------
# These classes are used to help indicate what elements the Interlinks class
# would return in a pandoc filter.


class Link(BaseModel):
    """Indicates a pandoc Link element."""

    kind: Literal["Link"] = "Link"
    content: str
    url: str


class Code(BaseModel):
    """Indicates a pandoc Code element."""

    kind: Literal["Code"] = "Code"
    content: str


class Unchanged(BaseModel):
    """Marker class for content that a function no-ops.

    The main purpose of this class is to indicate when a pandoc filter might
    return the original content element.
    """

    kind: Literal["Unchanged"] = "Unchanged"
    content: str


class TestSpecEntry(BaseModel):
    input: str
    output_text: Optional[str] = None
    output_link: Optional[str] = None
    output_element: Optional[
        Annotated[Union[Link, Code, Unchanged], Field(discriminator="kind")]
    ] = None
    error: Optional[str] = None
    warning: Optional[str] = None


class TestSpec(BaseModel):
    __root__: list[TestSpecEntry]


# Reference syntax ------------------------------------------------------------
# note that the classes above were made pydantic models so we could serialize
# them from json. We could make these ones pydantic too, but there is not a
# ton of benefit here.


@dataclass
class Ref:
    """Represent a sphinx-style reference.

    These have this format
        :external+<invname>:<domain>:<role>:`<target>`

    """

    target: "str"
    role: "None | str" = None
    domain: "None | str" = None
    invname: "None | str" = None

    external: bool = False

    @classmethod
    def from_string(cls, ref: str):
        if not (ref.startswith(":") or ref.startswith("`")):
            raise RefSyntaxError(
                'Ref must start with ":" or "`".\n' f"Received ref string: {ref}"
            )

        if not ref.endswith("`"):
            raise RefSyntaxError(
                'Ref must end with "`"\n' f"Received ref string: {ref}"
            )

        # Note that optional options after :external: go right-to-left.
        # e.g. :role:`target`
        # e.g. :external:role:`target`
        # e.g. :external:domain:role:`target`

        kwargs = {}

        # TODO: user may have omitted the starting `
        params, kwargs["target"], _ = ref.rsplit("`", 2)

        if params != "":
            if ref.startswith(":external"):
                external, *parts = params.lstrip(":").rstrip(":").split(":")

                kwargs["external"] = True
                if "+" in external:
                    kwargs["invname"] = external.split("+")[-1]
                else:
                    kwargs["invname"] = None

            else:
                kwargs["invname"] = None
                parts = params.lstrip(":").rstrip(":").split(":")

            kwargs.update(zip(["role", "domain"], reversed(parts)))

        return cls(**kwargs)


# Hold all inventory items in a singleton -------------------------------------


@dataclass
class EnhancedItem:
    # these are defined in the quarto config
    inv_name: str
    inv_url: str

    # these are defined in the inventory file itself
    name: str
    domain: str
    role: str
    priority: str
    uri: str
    dispname: str

    @property
    def full_uri(self):
        # TODO: this should only apply to a uri ending with "$"
        return self.inv_url + self.uri.replace("$", self.name)

    @classmethod
    def make_simple(cls, inv_name, full_url, name, role="function"):
        return cls(
            inv_name,
            "",
            name,
            domain="py",
            role=role,
            priority=1,
            uri=full_url,
            dispname="-",
        )


class Inventories:
    def __init__(self):
        self.registry: dict[str, list[EnhancedItem]] = {}

    def items(self):
        return itertools.chain(*self.registry.values())

    def load_inventory(self, inventory: dict, url: str, invname: str):
        all_items = []
        for item in inventory["items"]:
            # TODO: what are the rules for inventories with overlapping names?
            #       it seems like this is where priority and using source name as an
            #       optional prefix in references is useful (e.g. siuba:a.b.c).
            enh_item = EnhancedItem(inv_name=invname, inv_url=url, **item)
            all_items.append(enh_item)

        self.registry[invname] = all_items

    def lookup_reference(self, ref: Ref) -> EnhancedItem:
        """Return the item corresponding to a reference."""

        crnt_items = self.items()
        for field in ["name", "role", "domain", "invname"]:
            if field == "name":
                # target may have ~ option in front, so we strip it off
                field_value = ref.target.lstrip("~")
            else:
                field_value = getattr(ref, field)

            if field == "role":
                # for some reason, things like :func: are short for :function:.
                field_value = self.normalize_role(field_value)

            crnt_items = self._filter_by_field(crnt_items, field, field_value)

        results = list(crnt_items)
        if not results:
            raise InvLookupError(
                f"Cross reference not found in an inventory file: `{ref}`"
            )

        if len(results) > 1:
            raise InvLookupError(
                f"Cross reference matches multiple entries.\n"
                f"Matching entries: {len(results)}\n"
                f"Reference: {ref}\n"
                f"Top 2 matches: \n  * {results[0]}\n  * {results[1]}"
            )

        return results[0]

    def normalize_role(self, role_name):
        """Normalize the role portion of a reference."""

        if role_name == "func":
            return "function"

        return role_name

    def ref_to_anchor(self, ref: str | Ref, text: "str | None"):
        """Return a Link element based on a reference in interlink format

        Parameters
        ----------
        ref:
            The interlink reference (e.g. "my_module.my_function").
        text:
            The text to be displayed for the link.

        Examples
        --------

        >>> url = "https://example.org/functools.partial.html"
        >>> item = EnhancedItem.make_simple('someinv', url, name = 'functools.partial')
        >>> invs = Inventories.from_items([item])
        >>> invs.ref_to_anchor("functools.partial")
        Link(content='functools.partial', url='https://example.org/functools.partial.html')

        >>> invs.ref_to_anchor("~functools.partial")
        Link(content='partial', url='https://example.org/functools.partial.html')
        """

        if isinstance(ref, str):
            ref = Ref.from_string(ref)

        is_shortened = ref.target.startswith("~")

        entry = self.lookup_reference(ref)
        dst_url = entry.full_uri

        if not text:
            name = entry.name if entry.dispname == "-" else entry.dispname
            if is_shortened:
                # shorten names from module.sub_module.func_name -> func_name
                name = name.split(".")[-1]
            return Link(content=name, url=dst_url)

        return Link(content=text, url=dst_url)

    def pandoc_ref_to_anchor(self, ref: str, text: str) -> Link | Code | Unchanged:
        """Convert a ref to a Link, with special handling for pandoc filters.

        Note that this function is similar to ref_to_anchor, but handles pandoc's
        representation of ` as "%60", uses warnings instead of errors, and returns
        non-ref urls unchanged.
        """

        # detect what *might* be an interlink. note that we don't validate
        # that it has a closing `, to allow a RefSyntaxError to bubble up.
        if ref.startswith("%60") or ref.startswith(":"):
            # Get URL ----
            try:
                return self.ref_to_anchor(ref.replace("%60", "`"), text)
            except InvLookupError as e:
                warnings.warn(f"{e.__class__.__name__}: {e}")
                if text:
                    # Assuming content is a ListContainer(Str(...))
                    body = text
                else:
                    body = ref.replace("%60", "`")
                return Code(content=body)

        return Unchanged(content=ref)

    @staticmethod
    def _filter_by_field(items, field_name: str, value: "str | None" = None):
        if value is None:
            return items

        # TODO: Ref uses invname, while EnhancedItem uses inv_name
        if field_name == "invname":
            field_name = "inv_name"

        return (item for item in items if getattr(item, field_name) == value)

    @classmethod
    def from_items(cls, items: "list[EnhancedItem]"):
        invs = cls()
        for item in items:
            items = invs.registry.setdefault(item.inv_name, [])
            items.append(item)

        return invs

    @classmethod
    def from_quarto_config(cls, cfg: str | dict, root_dir: str | None = None):
        if isinstance(cfg, str):
            if root_dir is None:
                root_dir = Path(cfg).parent

            cfg = yaml.safe_load(open(cfg))

        invs = cls()
        p_root = get_path_to_root() if root_dir is None else Path(root_dir)

        interlinks = cfg["interlinks"]
        sources = interlinks["sources"]
        cache = interlinks.get("cache", "_inv")

        # load this sites inventory ----
        site_inv = interlinks.get("site_inv", "objects.json")

        json_data = json.load(open(p_root / site_inv))
        invs.load_inventory(json_data, url="/", invname="")

        # load other inventories ----
        for doc_name, cfg in sources.items():
            fname = doc_name + "_objects.json"
            inv_path = p_root / Path(cache) / fname

            json_data = json.load(open(inv_path))

            invs.load_inventory(json_data, url=cfg["url"], invname=doc_name)

        return invs
