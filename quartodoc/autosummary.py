import logging
import yaml

from functools import partial
from griffe.loader import GriffeLoader
from griffe.collections import ModulesCollection
from griffe.dataclasses import Alias
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds  # noqa
from griffe import dataclasses as dc
from plum import dispatch  # noqa
from pathlib import Path

from .inventory import create_inventory, convert_inventory
from .renderers import Renderer
from . import layout

from typing import Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import sphobjinv as soi


_log = logging.getLogger(__name__)


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


def get_object(
    module: str,
    object_name: str,
    parser: str = "numpy",
    load_aliases=True,
    modules_collection: "None | ModulesCollection" = None,
) -> dc.Object:
    """Fetch a griffe object.

    Parameters
    ----------
    module: str
        A module name.
    object_name: str
        A function name.
    parser: str
        A docstring parser to use.
    load_aliases: bool
        For aliases that were imported from other modules, should we load that module?
    modules_collection: optional
        A griffe [](`~griffe.collections.ModulesCollection`), used to hold loaded modules.

    See Also
    --------
    get_function: a deprecated function.

    Examples
    --------

    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    """
    griffe = GriffeLoader(
        docstring_parser=Parser(parser), modules_collection=modules_collection
    )
    mod = griffe.load_module(module)

    parts = object_name.split(".")
    f_data = mod._modules_collection[f"{module}.{object_name}"]

    # ensure that function methods fetched off of an Alias of a class, have that
    # class Alias as their parent, not the Class itself.
    if isinstance(f_data, dc.Function):
        try:
            parent_path = ".".join(parts[:-1])
            parent_alias = mod._modules_collection[f"{module}.{parent_path}"]
        except KeyError:
            pass
        else:
            f_data = dc.Alias(f_data.name, f_data, parent=parent_alias)

    # Alias objects can refer to objects imported from other modules.
    # in this case, we need to import the target's module in order to resolve
    # the alias
    if isinstance(f_data, Alias) and load_aliases:
        target_mod = f_data.target_path.split(".")[0]
        if target_mod != module:
            griffe.load_module(target_mod)

    return f_data


# pkgdown =====================================================================

# TODO: styles -- pkgdown, single-page, many-pages
class Builder:
    """Base class for building API docs.

    Parameters
    ----------
    package: str
        The name of the package.
    sections: ConfigSection
        A list of sections, with items to document.
    version:
        The package version. By default this attempts to look up the current package
        version (TODO).
    dir:
        Name of API directory.
    title:
        Title of the API index page.
    renderer: Renderer
        The renderer used to convert docstrings (e.g. to markdown).
    out_index:
        The output path of the index file, used to list all API functions.
    sidebar:
        The output path for a sidebar yaml config (by default no config generated).
    display_name: str
        The default name shown for documented functions. Either "name", "relative",
        "full", or "canonical". These options range from just the function name, to its
        full path relative to its package, to including the package name, to its
        the its full path relative to its `.__module__`.

    """

    # builder dispatching ----
    style: str
    _registry: "dict[str, Builder]" = {}

    # misc config
    out_inventory: str = "objects.json"
    out_index: str = "index.qmd"
    out_page_suffix = ".qmd"

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
        package: str,
        sections: "list[Any]",
        version: "str | None" = None,
        dir: str = "reference",
        title: str = "Function reference",
        renderer: "dict | Renderer | str" = "markdown",
        out_index: str = None,
        sidebar: "str | None" = None,
        use_interlinks: bool = False,
        display_name: str = "name",
    ):
        self.sections = self.load_sections(sections)
        self.package = package
        self.version = None
        self.dir = dir
        self.title = title
        self.display_name = display_name

        self.items: "list[layout.Item]"
        self.create_items()

        self.inventory: "None | soi.Inventory"
        self.create_inventory()

        self.renderer = Renderer.from_config(renderer)

        self.sidebar = sidebar

        if out_index is not None:
            self.out_index = out_index

        self.use_interlinks = use_interlinks

    def build(self):
        """Build index page, sphinx inventory, and individual doc pages."""

        _log.info("Rendering index")
        content = self.render_index()

        _log.info(f"Writing index to directory: {self.dir}")
        p_index = Path(self.dir) / self.out_index
        p_index.parent.mkdir(exist_ok=True, parents=True)
        p_index.write_text(content)

        _log.info(f"Saving inventory to {self.out_inventory}")
        convert_inventory(self.inventory, self.out_inventory)

        _log.info("Writing doc pages")
        self.write_doc_pages()

        if self.sidebar:
            _log.info(f"Writing sidebar yaml to {self.sidebar}")
            d_sidebar = self.generate_sidebar()
            yaml.dump(d_sidebar, open(self.sidebar, "w"))

    def load_sections(self, sections: dict):
        # TODO: currently returning the list of sections, to make work with
        # previous code. We should make Layout a first-class citizen of the
        # process.
        return layout.Layout(sections=sections).sections

    # introspection ----

    def create_items(self):
        """Collect items for all docstrings."""

        collection = ModulesCollection()
        f_get_object = partial(get_object, modules_collection=collection)

        _log.info("Creating items")

        ic = layout.ItemCollector(
            f_get_object, self.dir, self.package, self.display_name
        )
        ic.visit(self.sections)

        self.items = ic.results

    # inventory ----

    def create_inventory(self):
        """Generate sphinx inventory object."""

        # TODO: get package version
        _log.info("Creating inventory")
        version = "0.0.9999" if self.version is None else self.version
        self.inventory = create_inventory(
            self.package,
            version,
            self.items,
            self.fetch_object_uri,
            self.fetch_object_dispname,
        )

    def fetch_object_uri(self, obj, suffix=".html"):
        """Define the final url that will point to individual doc pages."""

        dispname = self.fetch_object_dispname(obj)
        return f"{self.dir}/{dispname}{suffix}"

    # rendering ----

    def render_index(self):
        """Generate API index page."""

        raise NotImplementedError()

    def render_item_link(self, obj):
        if self.use_interlinks:
            return f"[](`{obj.path}`)"

        link = "/" + self.fetch_object_uri(obj, suffix=self.out_page_suffix)
        name = self.fetch_object_dispname(obj)
        return f"[{name}]({link})"

    def write_doc_pages(self):
        """Write individual function documentation pages."""

        raise NotImplementedError()

    # sidebar ----

    def generate_sidebar(self):
        contents = [f"{self.dir}/{self.out_index}"]
        for section in self.sections:
            links = [
                self.fetch_object_uri(self.items[k], suffix=self.out_page_suffix)
                for k in section.contents
            ]

            contents.append({"section": section.title, "contents": links})

        return {"website": {"sidebar": {"id": self.dir, "contents": contents}}}

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
        rendered_sections = list(map(self.summarize, self.sections))
        str_sections = "\n\n".join(rendered_sections)

        return f"# {self.title}\n\n{str_sections}"

    @dispatch
    def summarize(self, el: layout.Section):
        header = f"## {el.title}\n\n{el.desc}"

        thead = "| | |\n| --- | --- |"

        rendered = []
        for func_name in el.contents:
            if isinstance(func_name, str):
                # TODO: shouldn't need to collect object again after .create_items()
                # TODO: transform step to handle getting objects
                obj = get_object(self.package, func_name)
            else:
                obj = func_name
            rendered.append(self.summarize(obj))

        str_func_table = "\n".join([thead, *rendered])
        return f"{header}\n\n{str_func_table}"

    @dispatch
    def summarize(self, el: layout.Page):
        if not el.flatten:
            # TODO: validate these attributes are set?
            return f"| [{el.name}]({el.path}) | {el.desc} |"

        else:
            return list(map(self.summarize, el.contents))

    @dispatch
    def summarize(self, obj: Union[dc.Object, dc.Alias]):
        # get high-level description
        doc = obj.docstring
        if doc is None:
            # TODO: add a single empty
            docstring_parts = []
        else:
            docstring_parts = doc.parsed

        # TODO: look up from inventory?
        link = self.render_item_link(obj)
        if len(docstring_parts) and isinstance(
            docstring_parts[0], ds.DocstringSectionText
        ):
            # TODO: or canonical_path
            description = docstring_parts[0].value
            short = description.split("\n")[0]
            return f"| {link} | {short} |"
        else:
            return f"| {link} | |"

    def write_doc_pages(self):
        for item in self.items.values():
            _log.info(f"Rendering `{item.canonical_path}`")
            rendered = self.renderer.render(item)
            html_path = Path(self.fetch_object_uri(item))
            html_path.parent.mkdir(exist_ok=True, parents=True)

            html_path.with_suffix(self.out_page_suffix).write_text(rendered)

    # def fetch_object_dispname(self, obj):
    #    return obj.name


class BuilderSinglePage(Builder):
    """Build an API with all docs embedded on a single page."""

    style = "single-page"

    def render_index(self):
        return "\n\n".join([self.renderer.render(item) for item in self.items.values()])

    def fetch_object_uri(self, obj):
        index_name = Path(self.out_index).with_suffix(".html")
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
