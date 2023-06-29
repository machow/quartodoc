import inspect
import griffe.dataclasses as dc

from typing import Any, get_type_hints

from .inspect import restify

from griffe.agents.inspector import _kind_map


def to_parameter(parameter: inspect.Parameter, annotation: Any) -> dc.Parameter:
    # adapted from griffe.agents.nodes
    # see LICENSES/griffe for ISC license
    name = parameter.name
    annotation = None if parameter.annotation is inspect.empty else restify(annotation)
    kind = _kind_map[parameter.kind]
    if parameter.default is inspect.empty:
        default = None
    elif hasattr(parameter.default, "__name__"):
        # avoid repr containing chevrons and memory addresses
        default = parameter.default.__name__
    else:
        default = repr(parameter.default)
    return dc.Parameter(name, annotation=annotation, kind=kind, default=default)


def to_function(f, name: "str | None" = None):
    from quartodoc.utils.convert import to_parameter
    from quartodoc.utils.inspect import restify

    from griffe.docstrings import Parser

    sig = inspect.signature(f)
    hints = get_type_hints(f)

    if name is None:
        name = getattr(f, "__qualname__")

    parameters = dc.Parameters(
        *[to_parameter(par, hints[k]) for k, par in sig.parameters.items()],
    )

    ret = hints.get("return") and restify(hints["return"])

    raw_doc = getattr(f, "__doc__", None)

    if raw_doc is None:
        doc = None
    else:
        doc = dc.Docstring(inspect.cleandoc(raw_doc), parser=Parser("numpy"))
    # TODO: should also be able to make into Alias

    kwargs = dict(name=name, parameters=parameters, returns=ret, docstring=doc)

    mod = inspect.getmodule(f)
    obj_mod = dc.Module(name=mod.__name__)

    return dc.Function(**kwargs, parent=obj_mod)


def maybe_alias(obj: dc.Object | dc.Alias, path: str) -> dc.Object | dc.Alias:
    if obj.path == path:
        return obj

    parent = dc.Module(name=path.split(".")[:-1])
    return dc.Alias(name=path.split(".")[-1], target=obj, parent=parent)
