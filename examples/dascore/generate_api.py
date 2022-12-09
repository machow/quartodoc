# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.6
#   kernelspec:
#     display_name: venv-quartodoc
#     language: python
#     name: venv-quartodoc
# ---

# +
from griffe import dataclasses as dc
from griffe.loader import GriffeLoader
from griffe.docstrings.parsers import Parser
from pathlib import Path
from plum import dispatch
from quartodoc import MdRenderer

griffe = GriffeLoader(docstring_parser=Parser("numpy"))
mod = griffe.load_module("dascore")

# +

# These functions don't render for one of two reasons: they contain a section
# type that is currently unsupported in the renderer (these are easy to add!),
# or due to a small bug with how annotations are rendered.
IGNORE = {
    "get_format",
    "write",
    "patches_to_df",
    "iter_files",
    "format_dtypes",
    "open_hdf5_file",
    "chunk",
    "get_intervals",
    "filter_df",
    "scan_to_df",
}

renderer = MdRenderer()


class AutoSummary:
    def __init__(self, dir_name: str):
        self.dir_name = dir_name

    @staticmethod
    def full_name(el):
        return f"{el.parent.canonical_path}.{el.name}"

    @dispatch
    def visit(self, el):
        raise TypeError(f"Unsupported type: {type(el)}")

    @dispatch
    def visit(self, el: dc.Module):
        print(f"MOD: {el.canonical_path}")
        for name, class_ in el.classes.items():
            self.visit(class_)

        for name, func in el.functions.items():
            self.visit(func)

        for name, mod in el.modules.items():
            self.visit(mod)

    @dispatch
    def visit(self, el: dc.Class):
        if el.name.startswith("_"):
            return

        print(f"CLASS: {self.full_name(el)}")
        for name, method in el.members.items():
            self.visit(method)

    @dispatch
    def visit(self, el: dc.Alias):
        # Should skip Aliases, since dascore API docs match its
        # filestructure.
        return None

    @dispatch
    def visit(self, el: dc.Function):
        if el.name.startswith("_"):
            return
        if el.name in IGNORE:
            return

        full_name = self.full_name(el)
        print(f"FUNCTION: {full_name}")

        p_root = Path(self.dir_name)
        p_root.mkdir(exist_ok=True)

        p_func = p_root / f"{full_name}.md"
        p_func.write_text(renderer.to_md(el))

    @dispatch
    def visit(self, el: dc.Attribute):
        if el.name.startswith("_"):
            return

        # a class attribute
        print(f"ATTR: {self.full_name(el)}")


# -

AutoSummary("api").visit(mod)
