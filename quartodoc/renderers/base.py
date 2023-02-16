import re

from plum import dispatch


# utils -----------------------------------------------------------------------


def escape(val: str):
    return f"`{val}`"


def sanitize(val: str):
    return val.replace("\n", " ")


def convert_rst_link_to_md(rst):
    expr = (
        r"((:external(\+[a-zA-Z\._]+))?(:[a-zA-Z\._]+)?:[a-zA-Z\._]+:`~?[a-zA-Z\._]+`)"
    )

    return re.sub(expr, r"[](\1)", rst, flags=re.MULTILINE)


# render -----------------------------------------------------------------------
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


class Renderer:
    style: str
    _registry: "dict[str, Renderer]" = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.style in cls._registry:
            raise KeyError(f"A builder for style {cls.style} already exists")

        cls._registry[cls.style] = cls

    @classmethod
    def from_config(cls, cfg: "dict | Renderer | str"):
        if isinstance(cfg, Renderer):
            return cfg
        elif isinstance(cfg, str):
            style, cfg = cfg, {}
        elif isinstance(cfg, dict):
            style = cfg["style"]
            cfg = {k: v for k, v in cfg.items() if k != "style"}
        else:
            raise TypeError(type(cfg))

        if style.endswith(".py"):
            import importlib

            mod = importlib.import_module(style.rsplit(".", 1)[0])
            return mod.Renderer(**cfg)

        subclass = cls._registry[style]
        return subclass(**cfg)

    @dispatch
    def render(self, el):
        raise NotImplementedError(f"render method does not support type: {type(el)}")
