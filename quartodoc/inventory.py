from __future__ import annotations

import sphobjinv as soi

from ._griffe_compat import dataclasses as dc
from plum import dispatch
from quartodoc import layout

from typing import Union, Callable


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


@dispatch
def _create_inventory_item(
    item: Union[dc.Object, dc.Alias],
    uri,
    dispname="-",
    priority="1",
) -> soi.DataObjStr:
    target = item

    return soi.DataObjStr(
        name=target.path,
        domain="py",
        role=target.kind.value,
        priority=priority,
        uri=_maybe_call(uri, target),
        dispname=_maybe_call(dispname, target),
    )


@dispatch
def _create_inventory_item(
    item: layout.Item, *args, priority="1", **kwargs
) -> soi.DataObjStr:
    return soi.DataObjStr(
        name=item.name,
        domain="py",
        role=item.obj.kind.value,
        priority=priority,
        uri=item.uri,
        dispname=item.dispname or "-",
    )


def _maybe_call(s: "str | Callable", obj):
    if callable(s):
        return s(obj)
    elif isinstance(s, str):
        return s

    raise TypeError(f"Expected string or callable, received: {type(s)}")
