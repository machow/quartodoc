import sphobjinv as soi

from griffe.loader import GriffeLoader
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc

from dataclasses import dataclass
from tabulate import tabulate

from plum import dispatch

from typing import Tuple, Union, Callable


# Set version =================================================================

from importlib_metadata import version as _v

__version__ = _v("quartodoc")

del _v


# Inventory files =============================================================
#
# inventories have this form:
# {
#   "project": "Siuba", "version": "0.4.2", "count": 2,
#   "items": [
#     {
#       "name": "siuba.dply.verbs.mutate",
#       "domain": "py",
#       "role": "function",
#       "priority": 0,
#       "uri": "api/verbs-mutate-transmute/",
#       "dispname": "-"
#     },
#    ...
#   ]
# }


# @click.command()
# @click.option("--in-name", help="Name of input inventory file")
# @click.option("--out-name", help="Name of result (defaults to <input_name>.json)")
def convert_inventory(in_name: "Union[str, soi.Inventory]", out_name=None):
    """Convert a sphinx inventory file to json.

    Parameters
    ----------
    in_name: str or sphobjinv.Inventory file
        Name of inventory file.
    out_name: str, optional
        Output file name.

    """

    import json
    from pathlib import Path

    if out_name is None:
        if isinstance(in_name, str):
            out_name = Path(in_name).with_suffix(".json")
        else:
            raise TypeError()

    if isinstance(in_name, soi.Inventory):
        inv = in_name
    else:
        inv = soi.Inventory(in_name)

    out = _to_clean_dict(inv)

    json.dump(out, open(out_name, "w"))


def create_inventory(
    project: str,
    version: str,
    items: "list[dc.Object | dc.Alias]",
    uri: "str | Callable[dc.Object, str]" = lambda s: f"{s.canonical_path}.html",
    dispname: "str | Callable[dc.Object, str]" = "-",
) -> soi.Inventory():
    """Return a sphinx inventory file.

    Parameters
    ----------
    project: str
        Name of the project (often the package name).
    version: str
        Version of the project (often the package version).
    items: str
        A docstring parser to use.
    uri:
        Link relative to the docs where the items documentation lives.
    dispname:
        Name to be shown when a link to the item is made.

    Examples
    --------

    >>> f_obj = get_object("quartodoc", "create_inventory")
    >>> inv = create_inventory("example", "0.0", [f_obj])
    >>> inv
    Inventory(project='example', version='0.0', source_type=<SourceTypes.Manual: 'manual'>)

    To preview the inventory, we can convert it to a dictionary:

    >>> _to_clean_dict(inv)
    {'project': 'example',
     'version': '0.0',
     'count': 1,
     'items': [{'name': 'quartodoc.create_inventory',
       'domain': 'py',
       'role': 'function',
       'priority': '1',
       'uri': 'quartodoc.create_inventory.html',
       'dispname': '-'}]}

    """

    inv = soi.Inventory()
    inv.project = project
    inv.version = version

    soi_items = [_create_inventory_item(x, uri, dispname) for x in items]

    inv.objects.extend(soi_items)

    return inv


def _to_clean_dict(inv: soi.Inventory):
    """Similar to Inventory.json_dict(), but with a list of items."""

    obj = inv.json_dict()

    long = list(obj.items())
    meta, entries = long[:3], [v for k, v in long[3:]]

    out = dict(meta)
    out["items"] = entries

    return out


def _create_inventory_item(
    item: "dc.Object | dc.Alias",
    uri: "str | Callable[dc.Object, str]",
    dispname: "str | Callable[dc.Object, str]" = "-",
    priority="1",
) -> soi.DataObjStr:
    if isinstance(item, dc.Alias):
        target = item.target
    else:
        target = item

    return soi.DataObjStr(
        name=target.canonical_path,
        domain="py",
        role=target.kind.value,
        priority=priority,
        uri=_maybe_call(uri, target),
        dispname=_maybe_call(dispname, target),
    )


def _maybe_call(s: "str | Callable", obj):
    if callable(s):
        return s(obj)
    elif isinstance(s, str):
        return s

    raise TypeError(f"Expected string or callable, received: {type(s)}")


# Docstring loading / parsing =================================================


def parse_function(module: str, func_name: str):
    griffe = GriffeLoader()
    mod = griffe.load_module(module)

    f_data = mod.functions[func_name]

    return parse(f_data.docstring, Parser.numpy)


def get_function(module: str, func_name: str, parser: str = "numpy") -> dc.Object:
    """Fetch a function.

    Parameters
    ----------
    module: str
        A module name.
    func_name: str
        A function name.
    parser: str
        A docstring parser to use.

    Examples
    --------

    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    """
    griffe = GriffeLoader(docstring_parser=Parser(parser))
    mod = griffe.load_module(module)

    f_data = mod.functions[func_name]

    return f_data


def get_object(module: str, object_name: str, parser: str = "numpy") -> dc.Object:
    """Fetch a griffe object.

    Parameters
    ----------
    module: str
        A module name.
    object_name: str
        A function name.
    parser: str
        A docstring parser to use.

    See Also
    --------
    get_function: a deprecated function.

    Examples
    --------

    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    """
    griffe = GriffeLoader(docstring_parser=Parser(parser))
    mod = griffe.load_module(module)

    f_data = mod._modules_collection[f"{module}.{object_name}"]

    return f_data


# Docstring rendering =========================================================

# utils -----------------------------------------------------------------------
# these largely re-format the output of griffe


def tuple_to_data(el: "tuple[ds.DocstringSectionKind, str]"):
    """Re-format funky tuple setup in example section to be a class."""
    assert len(el) == 2

    kind, value = el
    if kind.value == "examples":
        return ExampleCode(value)
    elif kind.value == "text":
        return ExampleText(value)

    raise ValueError(f"Unsupported first element in tuple: {kind}")


@dataclass
class ExampleCode:
    value: str


@dataclass
class ExampleText:
    value: str


def escape(val: str):
    return f"`{val}`"


# to_md -----------------------------------------------------------------------
# griffe function dataclass structure:
#   Object:
#     kind: Kind {"module", "class", "function", "attribute"}
#     name: str
#     docstring: Docstring
#     parent
#     path, canonical_path: str
#
#   Alias: wraps Object (_target) to lookup properties
#
#   Module, Class, Function, Attribute
#
# griffe docstring dataclass structure:
#   DocstringSection -> DocstringSection*
#   DocstringElement -> DocstringNamedElement -> Docstring*
#
#
# example templates:
#   https://github.com/mkdocstrings/python/tree/master/src/mkdocstrings_handlers/python/templates


class MdRenderer:
    """Render docstrings to markdown.

    Parameters
    ----------
    header_level: int
        The level of the header (e.g. 1 is the biggest).
    show_signature: bool
        Whether to show the function signature.

    Examples
    --------

    >>> from quartodoc import MdRenderer, get_object
    >>> renderer = MdRenderer(header_level=2)
    >>> f = get_object("quartodoc", "get_object")
    >>> print(renderer.to_md(f)[:81])
    ## get_object
    `get_object(module: str, object_name: str, parser: str = 'numpy')`

    """

    def __init__(
        self, header_level: int = 2, show_signature: bool = True, hook_pre=None
    ):
        self.header_level = header_level
        self.show_signature = show_signature
        self.hook_pre = hook_pre

    @dispatch
    def to_md(self, el):
        raise NotImplementedError(f"Unsupported type: {type(el)}")

    @dispatch
    def to_md(self, el: Union[dc.Alias, dc.Object]):
        # TODO: replace hard-coded header level

        _str_pars = self.to_md(el.parameters)
        str_sig = f"`{el.name}({_str_pars})`"

        _anchor = f"{{#sec-{ el.name }}}"
        str_title = f"{'#' * self.header_level} {el.name} {_anchor}"

        str_body = []
        if el.docstring is None:
            pass
        else:
            for section in el.docstring.parsed:
                title = section.kind.name
                body = self.to_md(section)

                if title != "text":
                    header = f"{'#' * (self.header_level + 1)} {title.title()}"
                    str_body.append("\n\n".join([header, body]))
                else:
                    str_body.append(body)

        if self.show_signature:
            parts = [str_title, str_sig, *str_body]
        else:
            parts = [str_title, *str_body]

        return "\n\n".join(parts)

    # signature parts -------------------------------------------------------------

    @dispatch
    def to_md(self, el: dc.Parameters):
        return ", ".join(map(self.to_md, el))

    @dispatch
    def to_md(self, el: dc.Parameter):
        # TODO: missing annotation
        splats = {dc.ParameterKind.var_keyword, dc.ParameterKind.var_positional}
        has_default = el.default and el.kind not in splats

        if el.annotation and has_default:
            return f"{el.name}: {el.annotation} = {el.default}"
        elif el.annotation:
            return f"{el.name}: {el.annotation}"
        elif has_default:
            return f"{el.name}={el.default}"

        return el.name

    # docstring parts -------------------------------------------------------------

    @dispatch
    def to_md(self, el: ds.DocstringSectionText):
        return el.value

    # parameters ----

    @dispatch
    def to_md(self, el: ds.DocstringSectionParameters):
        rows = list(map(self.to_md, el.value))
        header = ["Name", "Type", "Description", "Default"]
        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def to_md(self, el: ds.DocstringParameter) -> Tuple[str]:
        # TODO: if default is not, should return the word "required" (unescaped)
        default = "required" if el.default is None else escape(el.default)
        if isinstance(el.annotation, str):
            annotation = el.annotation
        else:
            annotation = el.annotation.full if el.annotation else None
        return (escape(el.name), annotation, el.description, default)

    # examples ----

    @dispatch
    def to_md(self, el: ds.DocstringSectionExamples):
        # its value is a tuple: DocstringSectionKind["text" | "examples"], str
        data = map(tuple_to_data, el.value)
        return "\n\n".join(list(map(self.to_md, data)))

    @dispatch
    def to_md(self, el: ExampleCode):
        return f"""```python
{el.value}
```"""

    # returns ----

    @dispatch
    def to_md(self, el: ds.DocstringSectionReturns):
        rows = list(map(self.to_md, el.value))
        header = ["Type", "Description"]
        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def to_md(self, el: ds.DocstringReturn):
        # similar to DocstringParameter, but no name or default
        annotation = el.annotation.full if el.annotation else None
        return (annotation, el.description)

    # unsupported parts ----

    @dispatch
    def to_md(self, el: ExampleText):
        return el.value

    @dispatch.multi(
        (ds.DocstringAdmonition,),
        (ds.DocstringDeprecated,),
        (ds.DocstringRaise,),
        (ds.DocstringWarn,),
        (ds.DocstringYield,),
        (ds.DocstringReceive,),
        (ds.DocstringAttribute,),
    )
    def to_md(self, el):
        raise NotImplementedError(f"{type(el)}")
