# Adapted from sphinx.util.inspect
# See LICENSES/sphinx for its two part BSD license

from __future__ import annotations

import itertools
import sys
import typing
from struct import Struct
from types import TracebackType
from typing import Any, ForwardRef, TypeVar, Union

from griffe.expressions import Name, Expression

try:
    from types import UnionType  # type: ignore  # python 3.10 or above
except ImportError:
    UnionType = None


# this is in types in python 3.10+
NoneType = type(None)

# builtin classes that have incorrect __module__
INVALID_BUILTIN_CLASSES = {
    Struct: "struct.Struct",  # Before Python 3.9
    TracebackType: "types.TracebackType",
}


def is_system_TypeVar(typ: Any) -> bool:
    """Check *typ* is system defined TypeVar."""
    modname = getattr(typ, "__module__", "")
    return modname == "typing" and isinstance(typ, TypeVar)


def is_invalid_builtin_class(obj: Any) -> bool:
    """Check *obj* is an invalid built-in class."""
    try:
        return obj in INVALID_BUILTIN_CLASSES
    except TypeError:  # unhashable type
        return False


def interleave(s: str, seq):
    """Return a sequence of seq joined with s

    Similar to s.join(seq), but without the conversion to a string.
    """

    seq = list(seq)

    if not len(seq):
        return []

    gen = itertools.chain(*zip([s] * len(seq), seq))
    next(gen)

    return gen


def to_expr(name: str, module=None, args=None):
    full = f"{module}.{name}" if module else name

    if args:
        if len(args) > 1:
            sub_expr = Expression(*args)
        else:
            sub_expr = args[0]

        return Expression(Name(name, full), "[", sub_expr, "]")

    return Name(name, full)


def restify(cls: type | None) -> str:
    """Convert python class to a reST reference.

    :param mode: Specify a method how annotations will be stringified.

                 'fully-qualified-except-typing'
                     Show the module name and qualified name of the annotation except
                     the "typing" module.
                 'smart'
                     Show the name of the annotation.
    """
    from sphinx.util import inspect  # lazy loading

    try:
        # Simple cases: None, Ellipsis, or a string ----
        if cls is None or cls is NoneType:
            return "None"
        elif cls is Ellipsis:
            return "..."
        elif isinstance(cls, str):
            return cls

        # More complex inference ----
        elif is_invalid_builtin_class(cls):
            raise NotImplementedError()
            # return f':py:class:`{INVALID_BUILTIN_CLASSES[cls]}`'
        elif inspect.isNewType(cls):
            if sys.version_info[:2] >= (3, 10):
                # newtypes have correct module info since Python 3.10+
                # class
                return Name(cls.__name__, f"{cls.__module__}.{cls.__name__}")
            else:
                return Name(cls.__name__, cls.__name__)
        elif UnionType and isinstance(cls, UnionType):
            if len(cls.__args__) > 1 and None in cls.__args__:
                parts = [restify(a) for a in cls.__args__ if a]
                children = Expression(*interleave("|", parts))

                return Expression(
                    Name("Optional", full="typing.Optional"), "[", children, "]"
                )
            else:
                return Expression(interleave("|", (restify(a) for a in cls.__args__)))
        elif cls.__module__ in ("__builtin__", "builtins"):
            if hasattr(cls, "__args__"):
                concatenated_args = interleave(
                    ",", (restify(arg) for arg in cls.__args__)
                )
                # TODO: griffe seems to make a sub-expression inside `[` only if
                # there are > 1 elements
                return Expression(
                    Name(cls.__name__, full=cls.__name__),
                    "[",
                    Expression(*concatenated_args),
                    "]",
                )
            else:
                return Name(cls.__name__, full=cls.__name__)
        elif (
            inspect.isgenericalias(cls)
            and cls.__module__ == "typing"
            and cls.__origin__ is Union
        ):  # type: ignore[attr-defined]
            if (
                len(cls.__args__) > 1  # type: ignore[attr-defined]
                and cls.__args__[-1] is NoneType
            ):  # type: ignore[attr-defined]
                if len(cls.__args__) > 2:  # type: ignore[attr-defined]
                    args = interleave(",", (restify(a) for a in cls.__args__[:-1]))
                    return Expression(
                        Name("Optional", "typing.Optional"),
                        "[",
                        Expression(Name("Union", "typing.Union"), "[", *args, "]",),
                        "]",
                    )
                else:
                    return Expression(
                        Name("Optional", "typing.Optional"),
                        "[",
                        restify(cls.__args__[0]),
                        "]",
                    )
            else:
                args = interleave(",", (restify(a) for a in cls.__args__))
                return Expression(Name("Union", "typing.Union"), "[", *args, "]")
        elif inspect.isgenericalias(cls):
            # This section consists of two steps: determining cls name and handling args
            # Step 1: class name ----
            if isinstance(cls.__origin__, typing._SpecialForm):  # type: ignore[attr-defined]
                name = restify(cls.__origin__)  # type: ignore
            elif getattr(cls, "_name", None):
                cls_name = cls._name  # type: ignore[attr-defined]
                if cls.__module__ == "typing":
                    name = Name(cls_name, f"{cls.__module__}.{cls_name}")
                else:
                    name = Name(cls_name, f"{cls.__module__}.{cls_name}")
            else:
                name = restify(cls.__origin__)  # type: ignore[attr-defined]

            # Step 2: handle args ----
            origin = getattr(cls, "__origin__", None)
            if not hasattr(cls, "__args__"):  # NoQA: SIM114
                pass
            elif all(is_system_TypeVar(a) for a in cls.__args__):
                # Suppress arguments if all system defined TypeVars (ex. Dict[KT, VT])
                pass
            elif (
                cls.__module__ == "typing" and cls._name == "Callable"
            ):  # type: ignore[attr-defined]
                args = ", ".join(restify(a) for a in cls.__args__[:-1])
                ret = restify(cls.__args__[-1])
                expr = Expression(name, "[", Expression("[", *args, "]", ret), "]")
            elif (
                cls.__module__ == "typing"
                and getattr(origin, "_name", None) == "Literal"
            ):
                args = interleave(",", [repr(a) for a in cls.__args__])
                expr = Expression(name, "[", Expression(*args), "]")
            elif cls.__args__:
                args = interleave(",", (restify(a) for a in cls.__args__))
                expr = Expression(name, "[", Expression(*args), "]")
            else:
                expr = None

            return expr if expr is not None else name
        elif isinstance(cls, typing._SpecialForm):
            return Name(cls._name, f"{cls.__module__}.{cls._name}")
        elif sys.version_info[:2] >= (3, 11) and cls is typing.Any:
            # handle bpo-46998
            return Name(cls.__name__, f"{cls.__module__}.{cls.__name__}")
        elif hasattr(cls, "__qualname__"):
            if cls.__module__ == "typing":
                return Name(cls.__qualname__, f"{cls.__module__}.{cls.__qualname__}")
            else:
                return Name(cls.__qualname__, f"{cls.__module__}.{cls.__qualname__}")
        elif isinstance(cls, ForwardRef):
            return Name(cls.__forward_arg__, cls.__forward_arg__)
        else:
            # not a class (ex. TypeVar)
            if cls.__module__ == "typing":
                return Name(cls.__name__, f"{cls.__module__}.{cls.__name__}")
            else:
                return Name(cls.__name__, f"{cls.__module__}.{cls.__name__}")
    except (AttributeError, TypeError):
        raise NotImplementedError(f"Cannot convert class to annotation: {cls}")
