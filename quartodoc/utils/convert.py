from __future__ import annotations

import inspect
import griffe.dataclasses as dc

from sphinx.util.typing import get_type_hints
from typing import Any

from .annotations import restify
from .inspect import get_module_members, is_valueless

from griffe.agents.inspector import _kind_map

from typing import TYPE_CHECKING

# from sphinx.ext.autodoc import ALL, EMPTY, UNINITIALIZED_ATTRIBUTE, INSTANCEATTR, SLOTSATTR
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from sphinx.ext.autodoc import ObjectMember


class MISSING_ANNOTATION:
    ...


def create_docstring(f) -> dc.Docstring | None:
    from griffe.docstrings import Parser

    raw_doc = inspect.getdoc(f)
    if raw_doc is None:
        doc = None
    else:
        doc = dc.Docstring(inspect.cleandoc(raw_doc), parser=Parser("numpy"))

    return doc


def to_parameter(parameter: inspect.Parameter, annotation: Any) -> dc.Parameter:
    # adapted from griffe.agents.nodes
    # see LICENSES/griffe for ISC license
    name = parameter.name
    annotation = None if parameter.annotation is inspect._empty else restify(annotation)

    kind = _kind_map[parameter.kind]
    if parameter.default is inspect._empty:
        default = None
    elif hasattr(parameter.default, "__name__"):
        # avoid repr containing chevrons and memory addresses
        default = parameter.default.__name__
    else:
        default = repr(parameter.default)
    return dc.Parameter(name, annotation=annotation, kind=kind, default=default)


def from_function(f, name: "str | None" = None, parent=None) -> dc.Function:
    sig = inspect.signature(f)
    hints = get_type_hints(f)

    if name is None:
        name = getattr(f, "__qualname__")

    parameters = dc.Parameters(
        *[to_parameter(par, hints.get(k, None)) for k, par in sig.parameters.items()],
    )

    ret = hints.get("return") and restify(hints["return"])

    doc = create_docstring(f)
    # TODO: should also be able to make into Alias

    kwargs = dict(name=name, parameters=parameters, returns=ret, docstring=doc)

    if parent is None:
        mod = inspect.getmodule(f)
        parent = dc.Module(name=mod.__name__)

    return dc.Function(**kwargs, parent=parent)


def from_class(obj, name, parent=None) -> dc.Class:
    doc = create_docstring(obj)
    data = dc.Class(name=name, parent=parent, docstring=doc)

    if obj is type:
        return data

    # add members ----
    raw_members = get_class_members(obj, name, safe_getattr)

    for name, child_obj in raw_members.items():
        child_data = dispatch(child_obj, parent=data)
        data.members[name] = child_data

        if name == "__dict__":
            continue

    return data


def from_module(obj, name, parent=None) -> dc.Module:
    doc = create_docstring(obj)
    data = dc.Module(name=name, parent=parent, docstring=doc)

    # add members ----
    raw_members = get_module_members(obj, name)

    for name, child_obj in raw_members.items():
        if name == "__dict__":
            continue

        child_data = dispatch(child_obj, parent=data)
        data.members[name] = child_data

    return data


def from_attribute(obj: ObjectMember, name, parent=None):
    # TODO: catch special sphinx types
    value = None if is_valueless(obj.object) else obj.object

    # modules and classes hold the type hints for their attributes
    hints = get_type_hints(obj.class_)
    hint = hints.get(name)
    expr = restify(hint)

    return dc.Attribute(name=name, value=value, annotation=expr, parent=parent)


def dispatch(obj: ObjectMember, parent):
    value = obj.object
    if inspect.ismodule(value):
        return from_module(value, obj.__name__, parent)
    if inspect.isclass(value):
        return from_class(value, obj.__name__, parent)
    if inspect.isfunction(value):
        return from_function(value, obj.__name__, parent)

    # unlike other constructors, making an attribute requires
    # the full object member, since we need to pull annotations
    # off of the parent module or class
    return from_attribute(obj, obj.__name__, parent)


def maybe_alias(obj: dc.Object | dc.Alias, path: str) -> dc.Object | dc.Alias:
    if obj.path == path:
        return obj

    parent = dc.Module(name=path.split(".")[:-1])
    return dc.Alias(name=path.split(".")[-1], target=obj, parent=parent)
