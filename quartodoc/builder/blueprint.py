from griffe import dataclasses as dc
from griffe.collections import ModulesCollection
from functools import partial

from plum import dispatch

from quartodoc.layout import _Base, Doc, Link, Auto, Section, Page, ChoicesChildren
from quartodoc import get_object as _get_object

from .utils import PydanticTransformer, ctx_node


class BlueprintTransformer(PydanticTransformer):
    def __init__(self, get_object=None):

        if get_object is None:
            collection = ModulesCollection()
            self.get_object = partial(_get_object, modules_collection=collection)

        self.crnt_package = None

    @dispatch
    def visit(self, el):
        # TODO: use a context handler
        self._log("VISITING", el)
        try:
            package = getattr(el, "package", None)

            old = self.crnt_package
            if package is not None:
                print(f"setting package to {package}")
                self.crnt_package = package
            return super().visit(el)
        finally:
            self.crnt_package = old

    @dispatch
    def exit(self, el: Doc):
        # potentially put doc on its own Page ----
        node = ctx_node.get()

        # top-level Lookups are level 4, since previous levels are:
        # layout, sections list, Section, contents list
        if node.level == 4 and isinstance(node.parent.parent.value, Section):
            return Page(contents=[el], path=el.name)

        return el

    @dispatch
    def enter(self, el: Auto):
        self._log("Entering", el)

        # TODO: make this less brittle
        obj = self.get_object(self.crnt_package, el.name)
        raw_members = self._fetch_members(el, obj)

        # Three cases for structuring child methods ----

        children = []
        for entry in raw_members:
            obj_member = self.get_object(obj.path, entry)

            # do no document submodules
            if obj_member.kind.value == "module":
                continue

            # create element for child ----
            autodoc = Doc.from_griffe(obj_member)

            # Case 1: make each member entry its own page
            if el.children == ChoicesChildren.separate:
                res = Page(path=obj_member.path, contents=[autodoc])
            # Case2: use just the Doc element, so it gets embedded directly
            # into the class being documented
            elif el.children == ChoicesChildren.embedded:
                res = autodoc
            # Case 3: make each member just a link in a summary table.
            # if the page for the member is not created somewhere else, then it
            # won't exist in the documentation (but its summary will still be in
            # the table).
            else:
                res = Link(name=obj_member.path, obj=obj_member)

            children.append(res)

        return Doc.from_griffe(obj, members=children)

    @staticmethod
    def _fetch_members(el: Auto, obj: dc.Object | dc.Alias):
        if el.members is not None:
            return el.members

        candidates = list(obj.members)

        if el.include:
            raise NotImplementedError("include argument currently unsupported.")
        elif el.exclude:
            raise NotImplementedError("exclude argument currently unsupported.")
        elif not el.include_private:
            return [meth for meth in candidates if not meth.startswith("_")]

        return candidates


class _PagePackageStripper(PydanticTransformer):
    def __init__(self, package: str):
        self.package = package

    @dispatch
    def exit(self, el: Page):
        parts = el.path.split(".")
        if parts[0] == self.package and len(parts) > 1:
            new_path = ".".join(parts[1:])
            new_el = el.copy()
            new_el.path = new_path
            return new_el

        return el


def strip_package_name(el: _Base, package: str):
    """Removes leading package name from layout Pages."""

    stripper = _PagePackageStripper(package)
    return stripper.visit(el)
