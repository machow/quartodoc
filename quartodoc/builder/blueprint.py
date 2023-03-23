import logging

from griffe import dataclasses as dc
from griffe.loader import GriffeLoader
from griffe.collections import ModulesCollection, LinesCollection
from griffe.docstrings.parsers import Parser
from functools import partial

from plum import dispatch

from quartodoc.layout import (
    MISSING,
    _Base,
    Auto,
    ChoicesChildren,
    Doc,
    Layout,
    Link,
    MemberPage,
    Page,
    Section,
)
from quartodoc import get_object as _get_object

from .utils import PydanticTransformer, ctx_node, WorkaroundKeyError

_log = logging.getLogger(__name__)


class BlueprintTransformer(PydanticTransformer):
    def __init__(self, get_object=None, parser="numpy"):

        if get_object is None:
            loader = GriffeLoader(
                docstring_parser=Parser(parser),
                modules_collection=ModulesCollection(),
                lines_collection=LinesCollection(),
            )
            self.get_object = partial(_get_object, loader=loader)
        else:
            self.get_object = get_object

        self.crnt_package = None

    def get_object_fixed(self, *args, **kwargs):
        try:
            return self.get_object(*args, **kwargs)
        except KeyError as e:
            raise WorkaroundKeyError(e.args[0])

    @dispatch
    def visit(self, el):
        # TODO: use a context handler
        self._log("VISITING", el)

        package = getattr(el, "package", MISSING())
        old = self.crnt_package

        if not isinstance(package, MISSING):
            self.crnt_package = package

        try:
            return super().visit(el)
        finally:
            self.crnt_package = old

    @dispatch
    def exit(self, el: Section):
        """Transform top-level sections, so their contents are all Pages."""

        node = ctx_node.get()

        # if we're not in a top-level section, then quit
        if not isinstance(node.parent.parent.value, Layout):
            return el

        # otherwise, replace all contents with pages.
        new = el.copy()
        contents = [
            Page(contents=[el], path=el.name) if isinstance(el, Doc) else el
            for el in new.contents
        ]

        new.contents = contents

        return new

    @dispatch
    def enter(self, el: Auto):
        self._log("Entering", el)

        # TODO: make this less brittle
        pkg = self.crnt_package
        if pkg is None:
            path = el.name
        else:
            path = f"{pkg}.{el.name}" if ":" in el.name else f"{pkg}:{el.name}"

        _log.info(f"Getting object for {path}")

        obj = self.get_object_fixed(path, dynamic=el.dynamic)
        raw_members = self._fetch_members(el, obj)

        # Three cases for structuring child methods ----

        children = []
        for entry in raw_members:
            # Note that we could have iterated over obj.members, but currently
            # if obj is an Alias to a class, then its members are not Aliases,
            # but the actual objects on the target.
            # On the other hand, we've wired get_object up to make sure getting
            # the member of an Alias also returns an Alias.
            obj_member = self.get_object_fixed(f"{path}.{entry}", dynamic=el.dynamic)

            # do no document submodules
            if obj_member.kind.value == "module":
                continue

            # create element for child ----
            doc = Doc.from_griffe(obj_member.name, obj_member)

            # Case 1: make each member entry its own page
            if el.children == ChoicesChildren.separate:
                res = MemberPage(path=obj_member.path, contents=[doc])
            # Case2: use just the Doc element, so it gets embedded directly
            # into the class being documented
            elif el.children == ChoicesChildren.embedded:
                res = doc
            # Case 3: make each member just a link in a summary table.
            # if the page for the member is not created somewhere else, then it
            # won't exist in the documentation (but its summary will still be in
            # the table).
            else:
                res = Link(name=obj_member.path, obj=obj_member)

            children.append(res)

        return Doc.from_griffe(el.name, obj, members=children)

    @staticmethod
    def _fetch_members(el: Auto, obj: dc.Object | dc.Alias):
        if el.members is not None:
            return el.members

        options = obj.members

        if el.include:
            raise NotImplementedError("include argument currently unsupported.")

        if el.exclude:
            raise NotImplementedError("exclude argument currently unsupported.")

        if not el.include_private:
            options = {k: v for k, v in options.items() if not k.startswith("_")}

        # for modules, remove any Alias objects, since they were imported from
        # other places. Sphinx has a flag for this behavior, so may be good
        # to do something similar.
        if obj.is_module:
            options = {k: v for k, v in options.items() if not v.is_alias}

        return sorted(options)


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
