import itertools
import json
import panflute as pf

from quartodoc.interlinks import Ref, RefSyntaxError
from pathlib import Path
from plum import dispatch


# Hold all inventory items in a singleton -------------------------------------

# TODO: make entries into dataclass
# has fields: name, domain, role, priority, invname, full_uri


class InvLookupError(Exception):
    pass


class Inventories:
    def __init__(self):
        self.registry = {}

    def items(self):
        return itertools.chain(*self.registry.values())

    def load_inventory(self, inventory, url, invname):
        all_items = []
        for item in inventory["items"]:
            # TODO: what are the rules for inventories with overlapping names?
            #       it seems like this is where priority and using source name as an
            #       optional prefix in references is useful (e.g. siuba:a.b.c).
            full_uri = url + item["uri"].replace("$", item["name"])
            enh_item = {**item, "invname": invname, "full_uri": full_uri}
            all_items.append(enh_item)

        self.registry[invname] = all_items

    def lookup_reference(self, ref: Ref):
        # return global_inventory[ref]

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

            crnt_items = _filter_by_field(crnt_items, field, field_value)

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
        if role_name == "func":
            return "function"

        return role_name


global_inventory = Inventories()


# Utility functions -----------------------------------------------------------


class ConfigError(Exception):
    pass


def get_path_to_root():
    # I have no idea how to get the documentation root,
    # except to get the path the extension script, which
    # lives in <root>/_extensions/interlinks, and work back
    p_root = Path(__file__).parent.parent.parent

    if p_root.name == "_extensions":
        return p_root.parent

    return p_root


def load_inventories(interlinks: dict):
    p_root = get_path_to_root()

    sources = interlinks["sources"]
    cache = interlinks.get("cache", "_inv")

    # load this sites inventory ----
    site_inv = interlinks.get("site_inv", "objects.json")

    json_data = json.load(open(p_root / site_inv))
    global_inventory.load_inventory(json_data, url="/", invname="")

    # load other inventories ----
    for doc_name, cfg in sources.items():

        fname = doc_name + "_objects.json"
        inv_path = p_root / Path(cache) / fname

        json_data = json.load(open(inv_path))

        global_inventory.load_inventory(json_data, url=cfg["url"], invname=doc_name)


def _filter_by_field(items, field_name: str, value: "str | None" = None):
    if value is None:
        return items

    return (item for item in items if item[field_name] == value)


def ref_to_anchor(raw: str, text: "str | pf.ListContainer | None"):
    """Return a Link element based on ref in interlink format

    Parameters
    ----------
    ref:
        The interlink reference (e.g. "my_module.my_function").
    text:
        The text to be displayed for the link.

    Examples
    --------

    >>> url = "https://example.org/functools.partial.html"
    >>> load_mock_inventory({"functools.partial": {"full_uri": url, "name": "functools.partial"}})
    >>> ref_to_anchor("functools.partial")
    Link(Str(functools.partial); url='https://example.org/functools.partial.html')

    >>> ref_to_anchor("~functools.partial")
    Link(Str(partial); url='https://example.org/functools.partial.html')
    """
    # TODO: for now we just mutate el

    try:
        ref = Ref.from_string(raw)
    except RefSyntaxError as e:
        pf.debug("WARNING: ", str(e))

    is_shortened = ref.target.startswith("~")

    entry = global_inventory.lookup_reference(ref)
    dst_url = entry["full_uri"]

    if not text:
        name = entry["name"] if entry["dispname"] == "-" else entry["dispname"]
        if is_shortened:
            # shorten names from module.sub_module.func_name -> func_name
            name = pf.Str(name.split(".")[-1])
        else:
            name = pf.Str(name)
    else:
        # when the element is an Link, content is a ListContainer, but it has to be
        # *splatted back into Link?
        if isinstance(text, pf.ListContainer):
            return pf.Link(*text, url=dst_url)
        elif isinstance(text, str):
            return pf.Link(pf.Str(text), url=dst_url)
        else:
            raise TypeError(f"Unsupported type: {type(text)}")

    return pf.Link(name, url=dst_url)


def parse_rst_style_ref(full_text):
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


# Visitor ================================================================================


def prepare(doc: pf.Doc):

    meta = doc.get_metadata()

    try:
        interlinks = meta["interlinks"]
    except KeyError:
        raise ConfigError(
            "No interlinks.sources field detected in your metadata."
            "Please add this to your header:\n\n"
            "interlinks:"
            "\n sources:"
            "\n    - <source_name>: {url: ..., inv: ..., fallback: ... }"
        )

    load_inventories(interlinks)

    return doc


@dispatch
def visit(el, doc):
    return el
    # raise TypeError(f"Unsupported type: {type(el)}")


# TODO: the syntax :ref:`target` is not trivial to implement. The pandoc AST
# often embeds it in a list of Plain with other elements. Currently, we only
# support the syntax inside of links.
#
# @dispatch
# def visit(el: pf.Plain, doc):
#     cont = el.content
#     if len(cont) == 2 and cont[0] == pf.Str(":ref:") and isinstance(cont[1], pf.Code):
#         _, code = el.content
#
#         ref, title = parse_rst_style_ref(code.text)
#
#         return pf.Plain(ref_to_anchor(ref, title))
#
#     return el


@dispatch
def visit(el: pf.Link, doc):
    url = el.url
    if (url.startswith("%60") or url.startswith(":")) and url.endswith("%60"):
        # Get URL ----
        try:
            return ref_to_anchor(url.replace("%60", "`"), el.content)
        except InvLookupError as e:
            pf.debug("WARNING: " + str(e))
            if el.content:
                # Assuming content is a ListContainer(Str(...))
                body = el.content[0].text
            else:
                body = url.replace("%60", "")
            return pf.Code(body)

    return el


def main(doc=None):
    return pf.run_filter(visit, prepare=prepare, doc=None)


if __name__ == "__main__":
    main()
