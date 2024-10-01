from __future__ import annotations

import warnings

from ._griffe_compat import docstrings as ds
from ._griffe_compat import dataclasses as dc

from enum import Enum
from dataclasses import dataclass
from plum import dispatch
from typing import Type, Union

from ._pydantic_compat import BaseModel  # for previewing

# Transform and patched-in classes ============================================
# TODO: annotate transform return types. make sure subtypes inherit from correct
# griffe base objects.
# TODO: it seems like transform should happen on the root, not individual elements.


def transform(el):
    """Return a more specific docstring element, or simply return the original one."""

    if isinstance(el, tuple):
        try:
            return tuple_to_data(el)
        except ValueError:
            pass

    # patch a list of docstring sections. note that this has to happen on the
    # list, since we replace single nodes on the tree (the list is the node).
    elif isinstance(el, list) and len(el) and isinstance(el[0], ds.DocstringSection):
        return _DocstringSectionPatched.transform_all(el)

    return el


# Patch DocstringSection ------------------------------------------------------


class DocstringSectionKindPatched(Enum):
    see_also = "see also"
    notes = "notes"
    warnings = "warnings"


class _DocstringSectionPatched(ds.DocstringSection):
    _registry: "dict[str, Type[_DocstringSectionPatched]]" = {}

    def __init__(self, value: str, title: "str | None" = None):
        super().__init__(title)
        self.value = value

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.kind.value in cls._registry:
            raise KeyError(f"A section for kind {cls.kind} already exists")

        cls._registry[cls.kind.value] = cls

    @staticmethod
    def split_sections(text) -> list[tuple[str, str]]:
        """Return tuples of (title, body) for all numpydoc style sections in the text.

        Note that this function does not check the value of the section header,
        only that it is a header on one line, with dashed on the next.
        """
        import re

        comp = re.compile(r"^([\S \t]+)\n-+$\n?", re.MULTILINE)

        crnt_match = comp.search(text)
        crnt_pos = 0

        # This loop takes a match, then attempts to look ahead at the next one,
        # in order to find the body of text between multiple sections.
        results = []
        while crnt_match is not None:
            # if the first section comes later in the text, ensure that we
            # create a section for the very beginning
            if crnt_pos == 0 and crnt_match.start() > 0:
                results.append(("", text[: crnt_match.start()]))

            next_pos = crnt_pos + crnt_match.end()
            substr = text[next_pos:]
            next_match = comp.search(substr)

            title = crnt_match.groups()[0]
            body = substr if next_match is None else substr[: next_match.start()]

            results.append((title, body))

            crnt_match, crnt_pos = next_match, next_pos

        return results

    @classmethod
    def transform(cls, el: ds.DocstringSection) -> list[ds.DocstringSection]:
        """Attempt to cast DocstringSection element to more specific section type.

        Note that this is meant to patch cases where the general DocstringSectionText
        class represents a section like See Also, etc..
        """

        if not isinstance(el, (ds.DocstringSectionText, ds.DocstringSectionAdmonition)):
            return [el]

        results = []

        # griffe < 0.39 w/ numpydoc uses DocstringSectionText for unhandled section
        # but later versions always use Admonitions. Note it may still use Text
        # for areas of docstrings not associated with particular sections (e.g. freeform
        # text betwen a parameters section and the next section).
        if isinstance(el, ds.DocstringSectionText):
            # handle griffe < 0.39 case
            splits = cls.split_sections(el.value)
            for title, body in splits:
                sub_cls = cls._registry.get(title.lower(), ds.DocstringSectionText)

                # note that griffe currently doesn't store the title anywhere,
                # but we add the exact title here, so we can be flexible about the
                # sections we parse (e.g. Note instead of Notes) in the future.
                results.append(sub_cls(body, title))
        elif isinstance(el, ds.DocstringSectionAdmonition):
            sub_cls = cls._registry.get(el.title.lower(), None)
            if sub_cls:
                results.append(sub_cls(el.value.contents, el.title))
            else:
                results.append(el)

        return results or [el]

    @classmethod
    def transform_all(cls, el: list[ds.DocstringSection]) -> list[ds.DocstringSection]:
        return sum(map(cls.transform, el), [])


class DocstringSectionSeeAlso(_DocstringSectionPatched):
    kind = DocstringSectionKindPatched.see_also


class DocstringSectionNotes(_DocstringSectionPatched):
    kind = DocstringSectionKindPatched.notes


class DocstringSectionWarnings(_DocstringSectionPatched):
    kind = DocstringSectionKindPatched.warnings


# Patch Example elements ------------------------------------------------------


@dataclass
class ExampleCode:
    value: str


@dataclass
class ExampleText:
    value: str


def tuple_to_data(el: "tuple[ds.DocstringSectionKind, str]"):
    """Re-format funky tuple setup in example section to be a class."""
    assert len(el) == 2

    kind, value = el
    if kind.value == "examples":
        return ExampleCode(value)
    elif kind.value == "text":
        return ExampleText(value)

    raise ValueError(f"Unsupported first element in tuple: {kind}")


# Tree previewer ==============================================================


@dispatch
def fields(el: BaseModel):
    # TODO: this is the only quartodoc specific code.
    # pydantic seems to copy MISSING() when it's a default, so we can't
    # whether a MISSING() is the default MISSING(). Instead, we'll just
    # use isinstance for this particular class
    from .layout import MISSING

    # return fields whose values were not set to the default
    field_defaults = {mf.name: mf.default for mf in el.__fields__.values()}
    return [
        k for k, v in el if field_defaults[k] is not v if not isinstance(v, MISSING)
    ]


@dispatch
def fields(el: dc.Object):
    options = [
        "name",
        "canonical_path",
        "classes",
        "parameters",
        "members",
        "functions",
        "docstring",
    ]
    return [opt for opt in options if hasattr(el, opt)]


@dispatch
def fields(el: dc.ObjectAliasMixin):
    try:
        return fields(el.target)
    except dc.AliasResolutionError:
        warnings.warn(
            f"Could not resolve Alias target `{el.target_path}`."
            " This often occurs because the module was not loaded (e.g. it is a"
            " package outside of your package)."
        )
        return ["name", "target_path"]


@dispatch
def fields(el: dc.Function):
    return ["name", "annotation", "parameters", "docstring"]


@dispatch
def fields(el: dc.Attribute):
    return ["name", "annotation"]


@dispatch
def fields(el: dc.Docstring):
    return ["parser", "parsed"]


@dispatch
def fields(el: ds.DocstringSection):
    return ["kind", "title", "value"]


@dispatch
def fields(el: ds.DocstringParameter):
    return ["annotation", "default", "description", "name", "value"]


@dispatch
def fields(el: ds.DocstringElement):
    return ["annotation", "description"]


@dispatch
def fields(el: ds.DocstringNamedElement):
    return ["name", "annotation", "description"]


@dispatch
def fields(el: dc.Parameter):
    return ["annotation", "kind", "name", "default"]


@dispatch
def fields(el: dict):
    return list(el.keys())


@dispatch
def fields(el: Union[list, dc.Parameters]):
    return list(range(len(el)))


@dispatch
def fields(el: object):
    if isinstance(el, (ExampleCode, ExampleText)):
        from dataclasses import fields as _fields

        return [field.name for field in _fields(el)]

    return None


class Formatter:
    n_spaces = 3
    icon_block = "█─"
    icon_pipe = "├─"
    icon_endpipe = "└─"
    icon_connector = "│ "
    string_truncate_mark = " ..."

    def __init__(self, string_max_length: int = 50, max_depth=999, compact=False):
        self.string_max_length = string_max_length
        self.max_depth = max_depth
        self.compact = compact

    def format(self, call, depth=0, pad=0):
        """Return a Symbolic or Call back as a nice tree, with boxes for nodes."""

        call = transform(call)

        crnt_fields = fields(call)

        if crnt_fields is None:
            str_repr = repr(call)
            if len(str_repr) > self.string_max_length:
                return str_repr[: self.string_max_length] + self.string_truncate_mark

            return str_repr

        call_str = self.icon_block + call.__class__.__name__

        # short-circuit for max depth ----
        if depth >= self.max_depth:
            return call_str + self.string_truncate_mark

        # format arguments ----
        fields_str = []
        for name in crnt_fields:
            val = self.get_field(call, name)

            # either align subfields with the end of the name, or put the node
            # on a newline, so it doesn't have to be so indented.
            if self.compact:
                sub_pad = pad
                linebreak = "\n" if fields(val) else ""
            else:
                sub_pad = len(str(name)) + self.n_spaces
                linebreak = ""

            # do formatting
            formatted_val = self.format(val, depth + 1, pad=sub_pad)
            fields_str.append(f"{name} = {linebreak}{formatted_val}")

        padded = []
        for ii, entry in enumerate(fields_str):
            is_final = ii == len(fields_str) - 1

            chunk = self.fmt_pipe(entry, is_final=is_final, pad=pad)
            padded.append(chunk)

        return "".join([call_str, *padded])

    def get_field(self, obj, k):
        if isinstance(obj, (dict, list, dc.Parameters)):
            return obj[k]

        return getattr(obj, k)

    def fmt_pipe(self, x, is_final=False, pad=0):
        if not is_final:
            connector = self.icon_connector if not is_final else "  "
            prefix = self.icon_pipe
        else:
            connector = "  "
            prefix = self.icon_endpipe

        connector = "\n" + " " * pad + connector
        prefix = "\n" + " " * pad + prefix
        # NOTE: because visiting is depth first, this is essentially prepending
        # the text to the left.
        return prefix + connector.join(x.splitlines())


def preview(
    ast: "dc.Object | ds.Docstring | object",
    max_depth=999,
    compact=False,
    as_string: bool = False,
):
    """Print a friendly representation of a griffe object (e.g. function, docstring)

    Examples
    --------

    >>> from quartodoc import get_object
    >>> obj = get_object("quartodoc", "get_object")

    >>> preview(obj.docstring.parsed)
    ...

    >>> preview(obj)
    ...

    """

    res = Formatter(max_depth=max_depth, compact=compact).format(ast)

    if as_string:
        return res

    print(res)
