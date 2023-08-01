"""quartodoc is a package for building delightful python API documentation.
"""

# flake8: noqa

from .autosummary import get_function, get_object, Builder
from .renderers import MdRenderer
from .inventory import convert_inventory, create_inventory
from .ast import preview
from .builder.blueprint import blueprint
from .builder.collect import collect
from .layout import Auto

__all__ = (
    "Auto",
    "blueprint",
    "collect",
    "convert_inventory",
    "create_inventory",
    "get_object",
    "preview",
    "Builder",
    "BuilderPkgdown",
    "BuilderSinglePage",
    "MdRenderer",
)
