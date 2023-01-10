from griffe.loader import GriffeLoader
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds  # noqa
from griffe import dataclasses as dc

from plum import dispatch  # noqa

from typing import Any


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


class Builder:
    pass


class BuilderPkgdown(Builder):
    def __init__(
        self,
        sections: "list[Any]",
        pkg_name: str,
        dir: str = "reference",
        title: str = "Function reference",
    ):
        self.validate(sections)

        self.sections = sections
        self.pkg_name = pkg_name
        self.dir = dir
        self.title = title

    def build(self):
        raise NotImplementedError()

    def render_index(self):
        rendered_sections = list(map(self.render_section, self.sections))
        str_sections = "\n\n".join(rendered_sections)

        return f"# {self.title}\n\n{str_sections}"

    def render_section(self, section):
        header = f"## {section['title']}\n\n{section['desc']}"

        thead = "| name | description |\n| --- | --- |"

        rendered = []
        for func_name in section["contents"]:
            obj = get_object(self.pkg_name, func_name)
            rendered.append(self.render_object(obj))

        str_func_table = "\n".join([thead, *rendered])
        return f"{header}\n\n{str_func_table}"

    def render_object(self, obj):
        # get high-level description
        docstring_parts = obj.docstring.parsed
        if len(docstring_parts):
            # TODO: or canonical_path
            name = obj.name
            description = docstring_parts[0].value
            short = description.split("\n")[0]
            return f"| {name} | {short} |"
        else:
            raise Exception("Function `{obj.canonical_path}` has no description")

    def validate(self, d):
        return True


"""
build:
  style: pkgdown
  dir: reference
  sections:
    - title: ...
      desc: ...
      contents:
        - some_func
        - another_func
    - title: ...
      desc: ...
      contents:
        - starts_with("...")
"""

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
