from enum import Enum
from dataclasses import dataclass
from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc
from plum import dispatch
from typing import Union


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
    elif isinstance(el, ds.DocstringSection):
        return _DocstringSectionPatched.transform(el)

    return el


# Patch DocstringSection ------------------------------------------------------


class DocstringSectionKindPatched(Enum):
    see_also = "see also"
    notes = "notes"
    warnings = "warnings"


class _DocstringSectionPatched(ds.DocstringSection):
    _registry: "dict[Enum, _DocstringSectionPatched]" = {}

    def __init__(self, value: str, title: "str | None" = None):
        self.value = value
        super().__init__(title)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.kind.value in cls._registry:
            raise KeyError(f"A section for kind {cls.kind} already exists")

        cls._registry[cls.kind] = cls

    @classmethod
    def transform(cls, el: ds.DocstringSection) -> ds.DocstringSection:
        """Attempt to cast DocstringSection element to more specific section type.

        Note that this is meant to patch cases where the general DocstringSectionText
        class represents a section like See Also, etc..
        """

        if isinstance(el, ds.DocstringSectionText):
            for kind, sub_cls in cls._registry.items():
                prefix = kind.value.title() + "\n---"
                if el.value.lstrip("\n").startswith(prefix):
                    stripped = el.value.replace(prefix, "", 1).lstrip("-\n")
                    return sub_cls(stripped, el.title)

        return el


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
    return fields(el.target)


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

    def __init__(self, string_max_length: int = 50, max_depth=999):
        self.string_max_length = string_max_length
        self.max_depth = max_depth

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
            formatted_val = self.format(
                val, depth + 1, pad=len(str(name)) + self.n_spaces
            )
            fields_str.append(f"{name} = {formatted_val}")

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


def preview(ast: "dc.Object | ds.Docstring | object", max_depth=999):
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
    print(Formatter(max_depth=max_depth).format(ast))
