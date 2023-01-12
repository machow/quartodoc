from griffe.loader import GriffeLoader
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds  # noqa
from griffe import dataclasses as dc
from plum import dispatch  # noqa
from pathlib import Path

from .inventory import create_inventory, convert_inventory
from .renderers import Renderer

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import sphobjinv as soi

    from griffe import dataclasses as dc


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


# pkgdown =====================================================================

# TODO: styles -- pkgdown, single-page, many-pages
class Builder:
    """Base class for building API docs.

    Parameters
    ----------
    sections: ConfigSection
        A list of sections, with items to document.
    package: str
        The name of the package.
    version:
        The package version. By default this attempts to look up the current package
        version (TODO).
    dir:
        Name of API directory.
    title:
        Title of the API index page.
    """

    # builder dispatching ----
    style: str
    _registry: "dict[str, Builder]" = {}

    # misc config
    out_inventory: str = "objects.json"
    out_index: str = "index.qmd"

    # quarto yaml config -----
    # TODO: add model for section with the fields:
    # title, desc, contents: list[str]
    sections: "list[Any]"
    package: str
    version: "str | None"
    dir: str
    title: str

    renderer: Renderer

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.style in cls._registry:
            raise KeyError(f"A builder for style {cls.style} already exists")

        cls._registry[cls.style] = cls

    def __init__(
        self,
        sections: "list[Any]",
        package: str,
        version: "str | None" = None,
        dir: str = "reference",
        title: str = "Function reference",
        renderer: "dict | Renderer | str" = "markdown",
    ):
        self.validate(sections)

        self.sections = sections
        self.package = package
        self.version = None
        self.dir = dir
        self.title = title

        self.items: "dict[str, dc.Object | dc.Alias]" = {}
        self.create_items()

        self.inventory: "None | soi.Inventory"
        self.create_inventory()

        self.renderer = Renderer.from_config(renderer)

    def build(self):
        """Build index page, sphinx inventory, and individual doc pages."""

        content = self.render_index()

        p_index = Path(self.dir) / self.out_index
        p_index.parent.mkdir(exist_ok=True, parents=True)
        p_index.write_text(content)

        convert_inventory(self.inventory, self.out_inventory)

        self.write_doc_pages()

    def validate(self, d):
        # TODO: validate sections (or config values generally)
        return True

    # introspection ----

    def create_items(self):
        """Collect items for all docstrings."""

        for section in self.sections:
            for func_name in section["contents"]:
                obj = get_object(self.package, func_name)
                self.items[obj.path] = obj

    # inventory ----

    def create_inventory(self):
        """Generate sphinx inventory object."""

        # TODO: get package version
        version = "0.0.9999" if self.version is None else self.version
        self.inventory = create_inventory(
            self.package,
            version,
            list(self.items.values()),
            self.fetch_object_uri,
            self.fetch_object_dispname,
        )

    def fetch_object_uri(self, obj):
        """Define the final url that will point to individual doc pages."""

        return f"{self.dir}/{obj.path}.html"

    def fetch_object_dispname(self, obj):
        """Define the name that will be displayed for individual api functions."""

        return obj.path

    # rendering ----

    def render_index(self):
        """Generate API index page."""

        raise NotImplementedError()

    def write_doc_pages(self):
        """Write individual function documentation pages."""

        # TODO: rename to_md to render or something
        for item in self.items.values():
            rendered = self.renderer.to_md(item)
            html_path = Path(self.fetch_object_uri(item))
            html_path.parent.mkdir(exist_ok=True, parents=True)

            html_path.with_suffix(".qmd").write_text(rendered)

    # constructors ----

    @classmethod
    def from_quarto_config(cls, quarto_cfg: "str | dict"):
        """Construct a Builder from a configuration object (or yaml file)."""

        # TODO: validation / config model loading
        if isinstance(quarto_cfg, str):
            import yaml

            quarto_cfg = yaml.safe_load(open(quarto_cfg))

        cfg = quarto_cfg["quartodoc"]
        style = cfg["style"]

        cls_builder = cls._registry[style]

        return cls_builder(**{k: v for k, v in cfg.items() if k != "style"})


class BuilderPkgdown(Builder):
    """Build an API in R pkgdown style.

    """

    style = "pkgdown"

    def render_index(self):
        rendered_sections = list(map(self._render_section, self.sections))
        str_sections = "\n\n".join(rendered_sections)

        return f"# {self.title}\n\n{str_sections}"

    def _render_section(self, section):
        header = f"## {section['title']}\n\n{section['desc']}"

        thead = "| | |\n| --- | --- |"

        rendered = []
        for func_name in section["contents"]:
            obj = get_object(self.package, func_name)
            rendered.append(self._render_object(obj))

        str_func_table = "\n".join([thead, *rendered])
        return f"{header}\n\n{str_func_table}"

    def _render_object(self, obj):
        # get high-level description
        doc = obj.docstring
        if doc is None:
            # TODO: add a single empty
            docstring_parts = []
        else:
            docstring_parts = doc.parsed

        # TODO: look up from inventory?
        link = f"[](`{obj.path}`)"
        if len(docstring_parts):
            # TODO: or canonical_path
            description = docstring_parts[0].value
            short = description.split("\n")[0]
            return f"| {link} | {short} |"
        else:
            return f"| {link} | |"

    def fetch_object_uri(self, obj):
        return f"{self.dir}/{obj.name}.html"

    def fetch_object_dispname(self, obj):
        return obj.name


class BuilderSinglePage(Builder):
    """Build an API with all docs embedded on a single page."""

    style = "single-page"

    def render_index(self):
        return "\n\n".join([self.renderer.to_md(item) for item in self.items])

    def fetch_object_uri(self, obj):
        index_name = Path(self.out_index).with_suffix("html")
        return f"{self.dir}/{index_name}#{obj.path}"

    def write_doc_pages(self):
        pass


# Builders ====================================================================

# renderer
# package name
# version
# api_directory
# exclude
# style: one-big-page, individual

# jobs:
#   - tracks paths to things (uri, dispname)

# phases:
#   - collect
#   - render (and record uri, dispname)
#   - compose autosummaries
#   - dump inventory

# build(object, config)
# build(Function, FunctionCfg)
# build(Class, ClsCfg)

# quartodoc
#   build:
#     - dir: api
#       module: "quartodoc"
#       include: ...
#       exclude: ["preview"]
#       overrides:


# quartodoc
#   module: "quartodoc"
#   style: one-big-page
#   sections:
#     - dir: api
#       include:
#         - preview


# quartodoc
#   module: "quartodoc"
#   style: many-pages
#   sections:
#     - file: api/ast.qmd
#       include:
#         - preview
#     - file: api/renderers.qmd
#       include:
#         - "
#   index:
#
# OR port pkgdown first
