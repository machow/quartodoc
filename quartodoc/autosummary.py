from __future__ import annotations

import inspect
import logging
import warnings
import yaml

from ._griffe_compat import GriffeLoader, ModulesCollection, LinesCollection
from ._griffe_compat import dataclasses as dc
from ._griffe_compat import Parser, parse

from fnmatch import fnmatchcase
from plum import dispatch  # noqa
from pathlib import Path
from types import ModuleType

from .inventory import create_inventory, convert_inventory
from . import layout
from .parsers import get_parser_defaults
from .renderers import Renderer
from .validation import fmt_all
from ._pydantic_compat import ValidationError
from .pandoc.blocks import Blocks, Header
from .pandoc.components import Attr


from typing import Any


_log = logging.getLogger(__name__)


# Docstring loading / parsing =================================================


def parse_function(module: str, func_name: str):
    griffe = GriffeLoader()
    mod = griffe.load(module)

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
    griffe = GriffeLoader(
        docstring_parser=Parser(parser), docstring_options=get_parser_defaults(parser)
    )
    mod = griffe.load(module)

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

    See Also
    --------
    preview: print a user-friendly preview of a griffe object.

    Examples
    --------

    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    Returns
    -------
    x:
        abc
    """

    if object_name is not None:
        warnings.warn(
            "object_name argument is deprecated in get_object", DeprecationWarning
        )

        path = f"{path}:{object_name}"

    if loader is None:
        loader = GriffeLoader(
            docstring_parser=Parser(parser),
            docstring_options=get_parser_defaults(parser),
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
        loader.load(module)

    # griffe uses only periods for the path
    griffe_path = f"{module}.{object_path}" if object_path else module

    # Case 1: dynamic loading ----
    if dynamic:
        if isinstance(dynamic, str):
            return dynamic_alias(path, target=dynamic, loader=loader)

        return dynamic_alias(path, loader=loader)

    # Case 2: static loading an object ----
    f_parent = loader.modules_collection[griffe_path.rsplit(".", 1)[0]]
    f_data = loader.modules_collection[griffe_path]

    # ensure that function methods fetched off of an Alias of a class, have that
    # class Alias as their parent, not the Class itself.
    if isinstance(f_parent, dc.Alias) and isinstance(
        f_data, (dc.Function, dc.Attribute)
    ):
        f_data = dc.Alias(f_data.name, f_data, parent=f_parent)

    # Alias objects can refer to objects imported from other modules.
    # in this case, we need to import the target's module in order to resolve
    # the alias
    if isinstance(f_data, dc.Alias) and load_aliases:
        target_mod = f_data.target_path.split(".")[0]
        if target_mod != module:
            loader.load(target_mod)

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
        for child_obj in obj.members.values():
            replace_docstring(child_obj)

    if f is None:
        mod = importlib.import_module(obj.module.canonical_path)

        if isinstance(obj.parent, dc.Class):
            parent_obj = getattr(mod, obj.parent.name)

            # we might fail to get the attribute if it is only a type annotation,
            # and in that case need to bail out of the docstring replacement
            try:
                f = getattr(parent_obj, obj.name)
            except AttributeError:
                return
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

    # get underlying object dynamically ----

    mod = importlib.import_module(mod_name)

    # Case 1: path is just to a module
    if object_path is None:
        attr = mod
        canonical_path = mod.__name__

    # Case 2: path is to a member of a module
    else:
        splits = object_path.split(".")

        canonical_path = None
        crnt_part = mod
        for ii, attr_name in enumerate(splits):
            # update canonical_path ----
            # this is our belief about where the final object lives (ie. its submodule)
            try:
                _qualname = ".".join(splits[ii:])
                new_canonical_path = _canonical_path(crnt_part, _qualname)
            except AttributeError:
                new_canonical_path = None

            if new_canonical_path is not None:
                # Note that previously we kept the first valid canonical path,
                # but now keep the last.
                canonical_path = new_canonical_path

            # fetch attribute ----
            try:
                crnt_part = getattr(crnt_part, attr_name)
            except AttributeError:
                # Fetching the attribute can fail if it is purely a type hint,
                # and has no value. This can be an issue if you have added a
                # docstring below the annotation
                if canonical_path:
                    # See if we can return the static object for a value-less attr
                    try:
                        obj = get_object(canonical_path, loader=loader)
                        if _is_valueless(obj):
                            return obj
                    except Exception as e:
                        # TODO: should we fail silently, so the error below triggers?
                        raise e

                raise AttributeError(
                    f"No attribute named `{attr_name}` in the path `{path}`."
                )

        # final canonical_path update ----
        # TODO: this is largely identical to canonical_path update above
        try:
            _qualname = ""
            new_canonical_path = _canonical_path(crnt_part, _qualname)
        except AttributeError:
            new_canonical_path = None

        if new_canonical_path is not None:
            # Note that previously we kept the first valid canonical path,
            # but now keep the last.
            canonical_path = new_canonical_path

        if canonical_path is None:
            raise ValueError(f"Cannot find canonical path for `{path}`")

        attr = crnt_part

    # start loading object with griffe ----

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

        parent = get_object(parent_path, loader=loader, dynamic=True)
        return dc.Alias(attr_name, obj, parent=parent)


def _canonical_path(crnt_part: object, qualname: str):
    suffix = (":" + qualname) if qualname else ""
    if not isinstance(crnt_part, ModuleType):
        # classes and functions ----
        if inspect.isclass(crnt_part) or inspect.isfunction(crnt_part):
            _mod = getattr(crnt_part, "__module__", None)

            if _mod is None:
                return None
            else:
                # we can use the object's actual __qualname__ here, which correctly
                # reports the path for e.g. methods on a class
                qual_parts = [] if not qualname else qualname.split(".")
                return _mod + ":" + ".".join([crnt_part.__qualname__, *qual_parts])
        elif isinstance(crnt_part, ModuleType):
            return crnt_part.__name__ + suffix
        else:
            return None
    else:
        # final object is module
        return crnt_part.__name__ + suffix


def _is_valueless(obj: dc.Object):
    if isinstance(obj, dc.Attribute):
        if (
            obj.labels.union({"class-attribute", "module-attribute"})
            and obj.value is None
        ):
            return True
        elif "instance-attribute" in obj.labels:
            return True

    return False


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
    options:
        Default options to set for all pieces of content (e.g. include_attributes).
    out_index:
        The output path of the index file, used to list all API functions.
    sidebar:
        The output path for a sidebar yaml config (by default no config generated).
    css:
        The output path for the default css styles.
    rewrite_all_pages:
        Whether to rewrite all rendered doc pages, or only those with changes.
    source_dir:
        A directory where source files to be documented live. This is only necessary
        if you are not documenting a package, but collection of scripts. Use a "."
        to refer to the current directory.
    dynamic:
        Whether to dynamically load all python objects. By default, objects are
        loaded using static analysis.
    render_interlinks:
        Whether to render interlinks syntax inside documented objects. Note that the
        interlinks filter is required to generate the links in quarto.
    parser:
        Docstring parser to use. This correspond to different docstring styles,
        and can be one of "google", "sphinx", and "numpy". Defaults to "numpy".

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
    package: str
    version: "str | None"
    dir: str
    title: str

    renderer: Renderer
    items: list[layout.Item]
    """Documented items by this builder"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.style in cls._registry:
            raise KeyError(f"A builder for style {cls.style} already exists")

        cls._registry[cls.style] = cls

    def __init__(
        self,
        package: str,
        # TODO: correct typing
        sections: "list[Any]" = tuple(),
        options: "dict | None" = None,
        version: "str | None" = None,
        dir: str = "reference",
        title: str = "Function reference",
        renderer: "dict | Renderer | str" = "markdown",
        out_index: str = None,
        sidebar: "str | None" = None,
        css: "str | None" = None,
        rewrite_all_pages=False,
        source_dir: "str | None" = None,
        dynamic: bool | None = None,
        parser="numpy",
        render_interlinks: bool = False,
        _fast_inventory=False,
    ):
        self.layout = self.load_layout(
            sections=sections, package=package, options=options
        )

        self.package = package
        self.version = None
        self.dir = dir
        self.title = title
        self.sidebar = sidebar
        self.css = css
        self.parser = parser

        self.renderer = Renderer.from_config(renderer)
        if render_interlinks:
            # this is a top-level option, but lives on the renderer
            # so we just manually set it there for now.
            self.renderer.render_interlinks = render_interlinks

        if out_index is not None:
            self.out_index = out_index

        self.rewrite_all_pages = rewrite_all_pages
        self.source_dir = str(Path(source_dir).absolute()) if source_dir else None
        self.dynamic = dynamic

        self._fast_inventory = _fast_inventory

    def load_layout(self, sections: dict, package: str, options=None):
        # TODO: currently returning the list of sections, to make work with
        # previous code. We should make Layout a first-class citizen of the
        # process.
        try:
            return layout.Layout(sections=sections, package=package, options=options)
        except ValidationError as e:
            msg = fmt_all(e)
            raise ValueError(msg) from None

    # building ----------------------------------------------------------------

    def build(self, filter: str = "*"):
        """Build index page, sphinx inventory, and individual doc pages.

        Parameters
        ----------
        filter:
            A simple pattern, that may include * as a wildcard. If specified,
            only doc paths for objects with matching names will be written.
            Path is the file's base name in the API dir (e.g. MdRenderer.render)
        """

        from quartodoc import blueprint, collect

        if self.source_dir:
            import sys

            sys.path.append(self.source_dir)

        # shaping and collection ----

        _log.info("Generating blueprint.")
        blueprint = blueprint(self.layout, dynamic=self.dynamic, parser=self.parser)

        _log.info("Collecting pages and inventory items.")
        pages, self.items = collect(blueprint, base_dir=self.dir)

        # writing pages ----

        _log.info("Writing index")
        self.write_index(blueprint)

        _log.info("Writing docs pages")
        self.write_doc_pages(pages, filter)
        self.renderer._pages_written(self)

        # inventory ----

        _log.info("Creating inventory file")
        inv = self.create_inventory(self.items)
        if self._fast_inventory:
            # dump the inventory file directly as text
            # TODO: copied from __main__.py, should add to inventory.py
            import sphobjinv as soi

            df = inv.data_file()
            soi.writebytes(Path(self.out_inventory).with_suffix(".txt"), df)

        else:
            convert_inventory(inv, self.out_inventory)

        # sidebar ----

        if self.sidebar:
            _log.info(f"Writing sidebar yaml to {self.sidebar}")
            self.write_sidebar(blueprint)

        # css ----

        if self.css:
            _log.info(f"Writing css styles to {self.css}")
            self.write_css()

    def write_index(self, blueprint: layout.Layout):
        """Write API index page."""

        _log.info("Summarizing docs for index page.")
        content = self.renderer.summarize(blueprint)
        _log.info(f"Writing index to directory: {self.dir}")

        final = str(
            Blocks([Header(1, self.title, Attr(classes=["doc", "doc-index"])), content])
        )

        p_index = Path(self.dir) / self.out_index
        p_index.parent.mkdir(exist_ok=True, parents=True)
        p_index.write_text(final)

        return str(p_index)

    def write_doc_pages(self, pages, filter: str):
        """Write individual function documentation pages."""

        for page in pages:
            _log.info(f"Rendering {page.path}")
            rendered = self.renderer.render(page)
            html_path = Path(self.dir) / (page.path + self.out_page_suffix)
            html_path.parent.mkdir(exist_ok=True, parents=True)

            # Only write out page if it has changed, or we've set the
            # rewrite_all_pages option. This ensures that quarto won't have
            # to re-render every page of the API all the time.
            if filter != "*":
                is_match = fnmatchcase(page.path, filter)

                if is_match:
                    _log.info("Matched filter")
                else:
                    _log.info("Skipping write (no filter match)")
                    continue

            if (
                self.rewrite_all_pages
                or (not html_path.exists())
                or (html_path.read_text() != rendered)
            ):
                _log.info(f"Writing: {page.path}")
                html_path.write_text(rendered)
            else:
                _log.info("Skipping write (content unchanged)")

    # inventory ----

    def create_inventory(self, items):
        """Generate sphinx inventory object."""

        # TODO: get package version
        _log.info("Creating inventory")
        version = "0.0.9999" if self.version is None else self.version
        inventory = create_inventory(self.package, version, items)

        return inventory

    # sidebar ----

    def _generate_sidebar(self, blueprint: layout.Layout):
        contents = [f"{self.dir}/index{self.out_page_suffix}"]
        in_subsection = False
        crnt_entry = {}
        for section in blueprint.sections:
            if section.title:
                if crnt_entry:
                    contents.append(crnt_entry)

                in_subsection = False
                crnt_entry = {"section": section.title, "contents": []}
            elif section.subtitle:
                in_subsection = True

            links = []
            for entry in section.contents:
                links.extend(self._page_to_links(entry))

            if in_subsection:
                sub_entry = {"section": section.subtitle, "contents": links}
                crnt_entry["contents"].append(sub_entry)
            else:
                crnt_entry["contents"].extend(links)

        if crnt_entry:
            contents.append(crnt_entry)

        entries = [{"id": self.dir, "contents": contents}, {"id": "dummy-sidebar"}]
        return {"website": {"sidebar": entries}}

    def write_sidebar(self, blueprint: layout.Layout):
        """Write a yaml config file for API sidebar."""

        d_sidebar = self._generate_sidebar(blueprint)
        yaml.dump(d_sidebar, open(self.sidebar, "w"))

    def write_css(self):
        """Write default css styles to a file."""
        from importlib_resources import files
        from importlib_metadata import version

        v = version("quartodoc")

        note = (
            f"/*\nThis file generated automatically by quartodoc version {v}.\n"
            "Modifications may be overwritten by quartodoc build. If you want to\n"
            "customize styles, create a new .css file to avoid losing changes.\n"
            "*/\n\n\n"
        )
        with open(files("quartodoc.static") / "styles.css") as f:
            Path(self.css).write_text(note + f.read())

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

        cfg = quarto_cfg.get("quartodoc")
        if cfg is None:
            raise KeyError("No `quartodoc:` section found in your _quarto.yml.")
        style = cfg.get("style", "pkgdown")
        cls_builder = cls._registry[style]

        _fast_inventory = quarto_cfg.get("interlinks", {}).get("fast", False)

        return cls_builder(
            **{k: v for k, v in cfg.items() if k != "style"},
            _fast_inventory=_fast_inventory,
        )


class BuilderPkgdown(Builder):
    """Build an API in R pkgdown style."""

    style = "pkgdown"


class BuilderSinglePage(Builder):
    """Build an API with all docs embedded on a single page."""

    style = "single-page"

    def load_layout(self, *args, **kwargs):
        el = super().load_layout(*args, **kwargs)

        el.sections = [layout.Page(path=self.out_index, contents=el.sections)]

        return el

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
