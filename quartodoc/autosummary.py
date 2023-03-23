from __future__ import annotations

import logging
import warnings
import yaml

from griffe.loader import GriffeLoader
from griffe.collections import ModulesCollection, LinesCollection
from griffe.dataclasses import Alias
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds  # noqa
from griffe import dataclasses as dc
from plum import dispatch  # noqa
from pathlib import Path
from types import ModuleType

from .inventory import create_inventory, convert_inventory
from . import layout
from .renderers import Renderer

from typing import Any, TYPE_CHECKING

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
    path: str,
    object_name: "str | None" = None,
    parser: str = "numpy",
    load_aliases=True,
    dynamic=False,
    loader: None | GriffeLoader = None,
) -> dc.Object:
    """Fetch a griffe object.

    Parameters
    ----------
    path: str
        An import path to the object. This should have the form `path.to.module:object`.
        For example, `quartodoc:get_object` or `quartodoc:MdRenderer.render`.
    object_name: str
        (Deprecated). A function name.
    parser: str
        A docstring parser to use.
    load_aliases: bool
        For aliases that were imported from other modules, should we load that module?
    dynamic: bool
        Whether to dynamically import object. Useful if docstring is not hard-coded,
        but was set on object by running python code.
    modules_collection: optional
        A griffe [](`~griffe.collections.ModulesCollection`), used to hold loaded modules.

    See Also
    --------
    preview: print a user-friendly preview of a griffe object.

    Examples
    --------

    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    """

    if object_name is not None:
        warnings.warn(
            "object_name argument is deprecated in get_object", DeprecationWarning
        )

        path = f"{path}:{object_name}"

    if loader is None:
        loader = GriffeLoader(
            docstring_parser=Parser(parser),
            modules_collection=ModulesCollection(),
            lines_collection=LinesCollection(),
        )

    try:
        module, object_path = path.split(":", 1)
    except ValueError:
        module, object_path = path, None

    # load the module if it hasn't been already.
    # note that it is critical for performance that we only do this when necessary.
    root_mod = module.split(".", 1)[0]
    if root_mod not in loader.modules_collection:
        loader.load_module(module)

    # griffe uses only periods for the path
    griffe_path = f"{module}.{object_path}"

    # Case 1: only getting a module ----
    if not object_path:
        return loader.modules_collection[module]

    # Case 2: dynamic loading ----
    if dynamic:
        if isinstance(dynamic, str):
            return dynamic_alias(path, target=dynamic, loader=loader)

        return dynamic_alias(path, loader=loader)

    # Case 3: static loading an object ----
    f_data = loader.modules_collection[griffe_path]
    f_parent = f_data.parent

    # ensure that function methods fetched off of an Alias of a class, have that
    # class Alias as their parent, not the Class itself.
    if isinstance(f_parent, dc.Alias) and isinstance(
        f_data, (dc.Function, dc.Attribute)
    ):
        f_data = dc.Alias(f_data.name, f_data, parent=f_parent)

    # Alias objects can refer to objects imported from other modules.
    # in this case, we need to import the target's module in order to resolve
    # the alias
    if isinstance(f_data, Alias) and load_aliases:
        target_mod = f_data.target_path.split(".")[0]
        if target_mod != module:
            loader.load_module(target_mod)

    return f_data


def _resolve_target(obj: dc.Alias):
    target = obj.target

    count = 0
    while isinstance(target, dc.Alias):
        count += 1
        if count > 100:
            raise ValueError(
                "Attempted to resolve target, but may be infinitely recursing?"
            )

        target = target.target

    return target


def replace_docstring(obj: dc.Object | dc.Alias, f=None):
    """Replace (in place) a docstring for a griffe object.

    Parameters
    ----------
    obj:
        Object to replace the docstring of.
    f:
        The python object whose docstring to use in the replacement. If not
        specified, then attempt to import obj and use its docstring.

    """
    import importlib

    if isinstance(obj, dc.Alias):
        obj = _resolve_target(obj)

    # for classes, we dynamically load the docstrings for all their methods.
    # since griffe reads class docstrings from the .__init__ method, this should
    # also have the effect of updating the class docstring.
    if isinstance(obj, dc.Class):
        for func_obj in obj.functions.values():
            replace_docstring(func_obj)

    if f is None:
        mod = importlib.import_module(obj.module.canonical_path)

        if isinstance(obj.parent, dc.Class):
            f = getattr(getattr(mod, obj.parent.name), obj.name)
        else:
            f = getattr(mod, obj.name)

    # if no docstring on the dynamically loaded function, then stop
    # since there's nothing to update.
    # TODO: A static docstring could have been detected erroneously
    if f.__doc__ is None:
        return

    old = obj.docstring
    new = dc.Docstring(
        value=f.__doc__,
        lineno=getattr(old, "lineno", None),
        endlineno=getattr(old, "endlineno", None),
        parent=getattr(old, "parent", None),
        parser=getattr(old, "parser", None),
        parser_options=getattr(old, "parser_options", None),
    )

    obj.docstring = new


def dynamic_alias(
    path: str, target: "str | None" = None, loader=None
) -> dc.Object | dc.Alias:
    """Return and Alias, using a dynamic import to find the target.

    Parameters
    ----------
    path:
        Full path to the object. E.g. `quartodoc.get_object`.
    get_object_:
        Function used to fetch the alias target.
    target:
        Optional path to ultimate Alias target. By default, this is inferred
        using the __module__ attribute of the imported object.

    """
    import importlib

    # TODO: raise an informative error if no period
    try:
        mod_name, object_path = path.split(":", 1)
    except ValueError:
        mod_name, object_path = path, None

    mod = importlib.import_module(mod_name)

    # Case 1: path is just to a module
    if object_path is None:
        attr = get_object(path)
        canonical_path = attr.__name__

    # Case 2: path is to a member of a module
    else:
        splits = object_path.split(".")

        canonical_path = None
        parts = []
        crnt_part = mod
        for ii, attr_name in enumerate(splits):
            try:
                crnt_part = getattr(crnt_part, attr_name)
                if not isinstance(crnt_part, ModuleType) and not canonical_path:
                    canonical_path = crnt_part.__module__ + ":" + ".".join(splits[ii:])

                parts.append(crnt_part)
            except AttributeError:
                raise AttributeError(
                    f"No attribute named `{attr_name}` in the path `{path}`."
                )

        if canonical_path is None:
            raise ValueError("Cannot find canonical path for `{path}`")

        attr = crnt_part

    # start loading things with griffe ----

    if target:
        obj = get_object(target, loader=loader)
    else:
        obj = get_object(canonical_path, loader=loader)

    # use dynamically imported object's docstring
    replace_docstring(obj, attr)

    if obj.canonical_path == path.replace(":", "."):
        return obj
    else:
        # TODO: this logic should live in a MemberPath dataclass or something
        if object_path:
            if "." in object_path:
                prev_member = object_path.rsplit(".", 1)[0]
                parent_path = f"{mod_name}:{prev_member}"
            else:
                parent_path = mod_name
        else:
            parent_path = mod_name.rsplit(".", 1)[0]

        parent = get_object(parent_path, loader=loader)
        return dc.Alias(attr_name, obj, parent=parent)


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
        rewrite_all_pages=True,
    ):
        self.layout = self.load_layout(sections=sections, package=package)
        self.sections = self.layout.sections

        self.package = package
        self.version = None
        self.dir = dir
        self.title = title
        self.display_name = display_name

        self.items: "list[layout.Item]"
        # self.create_items()

        self.inventory: "None | soi.Inventory"
        # self.create_inventory()

        self.renderer = Renderer.from_config(renderer)

        self.sidebar = sidebar

        if out_index is not None:
            self.out_index = out_index

        self.use_interlinks = use_interlinks
        self.rewrite_all_pages = rewrite_all_pages

    def load_layout(self, sections: dict, package: str):
        # TODO: currently returning the list of sections, to make work with
        # previous code. We should make Layout a first-class citizen of the
        # process.
        return layout.Layout(sections=sections, package=package)

    # building ----------------------------------------------------------------

    def build(self):
        """Build index page, sphinx inventory, and individual doc pages."""

        # shaping and collection ----

        _log.info("Generating blueprint.")
        blueprint = self.do_blueprint()

        _log.info("Collecting pages and inventory items.")
        pages, items = self.do_collect(blueprint)

        # strip package name the item name, so that it isn't repeated a ton
        # in our internal docs links.
        stripped_items = self._strip_item_dispname(items)

        _log.info("Summarizing docs for index page.")
        summary = self.do_summarize(blueprint, stripped_items)

        # writing pages ----

        _log.info("Writing index")
        self.write_index(summary)

        _log.info("Writing docs pages")
        self.write_doc_pages(pages, stripped_items)

        # inventory ----

        _log.info("Creating inventory file")
        inv = self.create_inventory(items)
        convert_inventory(inv, self.out_inventory)

        # sidebar ----

        if self.sidebar:
            _log.info(f"Writing sidebar yaml to {self.sidebar}")
            d_sidebar = self.generate_sidebar(blueprint)
            yaml.dump(d_sidebar, open(self.sidebar, "w"))

    def do_blueprint(self) -> layout.Layout:
        """Convert a layout with Auto elements to a full-fledged doc specification."""

        from quartodoc.builder.blueprint import BlueprintTransformer

        bt = BlueprintTransformer()
        blueprint = bt.visit(self.layout)

        return blueprint

    def do_collect(self, blueprint) -> tuple[list[layout.Page], list[layout.Item]]:
        """Collect the pages and sphinx item information from a layout."""

        from quartodoc.builder.collect import CollectTransformer

        ct = CollectTransformer(self.dir)
        ct.visit(blueprint)

        return ct.pages, ct.items

    def do_summarize(self, blueprint, items):
        """Summarize a layout into index tables."""

        summary = self.renderer.summarize(blueprint)

        return summary

    def write_index(self, content: str):
        """Write API index page."""

        _log.info(f"Writing index to directory: {self.dir}")

        final = f"# {self.title}\n\n{content}"

        p_index = Path(self.dir) / self.out_index
        p_index.parent.mkdir(exist_ok=True, parents=True)
        p_index.write_text(final)

        return str(p_index)

    def write_doc_pages(self, pages, items):
        """Write individual function documentation pages."""

        for page in pages:
            _log.info(f"Rendering {page.path}")
            rendered = self.renderer.render(page)
            html_path = Path(self.dir) / (page.path + self.out_page_suffix)
            html_path.parent.mkdir(exist_ok=True, parents=True)

            # Only write out page if it has changed, or we've set the
            # rewrite_all_pages option. This ensures that quarto won't have
            # to re-render every page of the API all the time.
            if (
                self.rewrite_all_pages
                or (not html_path.exists())
                or (html_path.read_text() != rendered)
            ):
                html_path.write_text(rendered)

    # inventory ----

    def create_inventory(self, items):
        """Generate sphinx inventory object."""

        # TODO: get package version
        _log.info("Creating inventory")
        version = "0.0.9999" if self.version is None else self.version
        inventory = create_inventory(self.package, version, items)

        return inventory

    def _strip_item_dispname(self, items):
        result = []
        for item in items:
            new = item.copy()
            prefix = self.package + "."
            if new.name.startswith(prefix):
                new.dispname = new.name.replace(prefix, "", 1)
            result.append(new)

        return result

    # sidebar ----

    def generate_sidebar(self, blueprint: layout.Layout):
        contents = [f"{self.dir}/{self.out_index}"]
        for section in blueprint.sections:
            links = []
            for entry in section.contents:
                links.extend(self._page_to_links(entry))

            contents.append({"section": section.title, "contents": links})

        return {"website": {"sidebar": {"id": self.dir, "contents": contents}}}

    def _page_to_links(self, el: layout.Page) -> list[str]:
        # if el.flatten:
        #     links = []
        #     for entry in el.contents:
        #         links.append(f"{self.dir}/{entry.path}{self.out_page_suffix}")
        #     return links

        return [f"{self.dir}/{el.path}{self.out_page_suffix}"]

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


class BuilderSinglePage(Builder):
    """Build an API with all docs embedded on a single page."""

    style = "single-page"

    def load_layout(self, *args, **kwargs):
        el = super().load_layout(*args, **kwargs)

        el.sections = [layout.Page(path=self.out_index, contents=el.sections)]

        return el

    def do_summarize(self, *args, **kwargs):
        pass

    def write_index(self, *args, **kwargs):
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
