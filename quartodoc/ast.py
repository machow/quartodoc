from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc
from plum import dispatch
from typing import Union

# TODO: these classes are created to wrap some tuple outputs
#       we should consolidate logic for transforming the griffe
#       docstring here (or open a griffe issue).
from .renderers import tuple_to_data, docstring_section_narrow, ExampleCode, ExampleText


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

        call = self.transform(call)

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

    def transform(self, obj):
        # TODO: currently this transform happens here, and in the renderer.
        #       let's consolidate this into one step (when getting the object)
        if isinstance(obj, tuple):
            try:
                return tuple_to_data(obj)
            except ValueError:
                pass
        elif isinstance(obj, ds.DocstringSectionText):
            return docstring_section_narrow(obj)

        return obj

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
