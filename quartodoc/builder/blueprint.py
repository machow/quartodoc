from __future__ import annotations

import logging
import json
import yaml

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

from typing import overload

_log = logging.getLogger(__name__)


def _auto_package(mod: dc.Module) -> list[Section]:
    """Create default sections for the given package."""

    import griffe.docstrings.dataclasses as ds

    # get module members for content ----
    contents = []
    for name, member in mod.members.items():
        external_alias = _is_external_alias(member, mod)
        if external_alias or member.is_module or name.startswith("__"):
            continue

        contents.append(Auto(name=name))

    # try to fetch a description of the module ----
    mod_summary = mod.docstring.parsed[0]
    if isinstance(mod_summary, ds.DocstringSectionText):
        desc = mod_summary.value
    else:
        desc = ""

    return [Section(title=mod.name, desc=desc, contents=contents)]


def _is_external_alias(obj: dc.Alias | dc.Object, mod: dc.Module):
    package_name = mod.name.split(".")[0]

    if not isinstance(obj, dc.Alias):
        return False

    crnt_target = obj

    while crnt_target.is_alias:
        if not crnt_target.target_path.startswith(package_name):
            return True

        try:
            new_target = crnt_target.modules_collection.get_member(
                crnt_target.target_path
            )
            if new_target is crnt_target:
                raise Exception(f"Cyclic Alias: {new_target}")

            crnt_target = new_target

        except KeyError:
            # assumes everything from module was loaded, so target must
            # be outside module
            return True

    return False


def _to_simple_dict(el):
    # round-trip to json, so we can take advantage of pydantic
    # dumping Enums, etc.. There may be a simple way to do
    # this in pydantic v2.
    return json.loads(el.json(exclude_unset=True))


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
        self.dynamic = None

    @staticmethod
    def _append_member_path(path: str, new: str):
        if ":" in path:
            return f"{path}.{new}"

        return f"{path}:{new}"

    def get_object_fixed(self, path, **kwargs):
        try:
            return self.get_object(path, **kwargs)
        except KeyError as e:
            key_name = e.args[0]
            raise WorkaroundKeyError(
                f"Cannot find an object named: {key_name}."
                f" Does an object with the path {path} exist?"
            )

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
    def enter(self, el: Layout):
        if not el.sections:
            # TODO: should be shown all the time, not just logged,
            # but also want to be able to disable (similar to pins)
            print("Autogenerating contents (since no contents specified in config)")

            package = el.package

            mod = self.get_object_fixed(package)
            sections = _auto_package(mod)

            if not sections:
                # TODO: informative message. When would this occur?
                raise ValueError()

            new_el = el.copy()
            new_el.sections = sections

            print(
                "Use the following configuration to recreate the automatically",
                " generated site:\n\n\n",
                yaml.safe_dump(_to_simple_dict(new_el)),
                "\n",
                sep="",
            )

            return super().enter(new_el)

        return super().enter(el)

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
            Page(contents=[el], path=el.name) if not isinstance(el, Page) else el
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

        dynamic = el.dynamic if el.dynamic is not None else self.dynamic

        obj = self.get_object_fixed(path, dynamic=dynamic)
        raw_members = self._fetch_members(el, obj)

        # Three cases for structuring child methods ----

        children = []
        for entry in raw_members:
            # Note that we could have iterated over obj.members, but currently
            # if obj is an Alias to a class, then its members are not Aliases,
            # but the actual objects on the target.
            # On the other hand, we've wired get_object up to make sure getting
            # the member of an Alias also returns an Alias.
            member_path = self._append_member_path(path, entry)
            obj_member = self.get_object_fixed(member_path, dynamic=dynamic)

            # do no document submodules
            if (
                _is_external_alias(obj_member, obj.package)
                or obj_member.kind.value == "module"
            ):
                continue

            # create element for child ----
            doc = Doc.from_griffe(obj_member.name, obj_member)

            # Case 1: make each member entry its own page
            if el.children == ChoicesChildren.separate:
                res = MemberPage(path=obj_member.path, contents=[doc])
            # Case2: use just the Doc element, so it gets embedded directly
            # into the class being documented
            elif el.children in {ChoicesChildren.embedded, ChoicesChildren.flat}:
                res = doc
            # Case 3: make each member just a link in a summary table.
            # if the page for the member is not created somewhere else, then it
            # won't exist in the documentation (but its summary will still be in
            # the table).
            elif el.children == ChoicesChildren.linked:
                res = Link(name=obj_member.path, obj=obj_member)
            else:
                raise ValueError(f"Unsupported value of children: {el.children}")

            children.append(res)

        is_flat = el.children == ChoicesChildren.flat
        return Doc.from_griffe(el.name, obj, members=children, flat=is_flat)

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
        # if obj.is_module:
        #    options = {k: v for k, v in options.items() if not v.is_alias}

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


@overload
def blueprint(el: Auto, package: str) -> Doc:
    ...


def blueprint(
    el: _Base, package: str = None, dynamic: None | bool = None, parser="numpy"
) -> _Base:
    """Convert a configuration element to something that is ready to render.

    Parameters
    ----------
    el:
        An element, like layout.Auto, to transform.
    package:
        A base package name. If specified, this is prepended to the names of any objects.
    dynamic:
        Whether to dynamically load objects. Defaults to using static analysis.

    Examples
    --------

    >>> from quartodoc import blueprint
    >>> from quartodoc.layout import Auto
    >>> blueprint(Auto(name = "quartodoc.get_object"))
    DocFunction(name='quartodoc.get_object', ...)

    >>> blueprint(Auto(name = "get_object"), package = "quartodoc")
    DocFunction(name='get_object', ...)

    """

    trans = BlueprintTransformer(parser=parser)

    if package is not None:
        trans.crnt_package = package

    if dynamic is not None:
        trans.dynamic = dynamic

    return trans.visit(el)


def strip_package_name(el: _Base, package: str):
    """Removes leading package name from layout Pages."""

    stripper = _PagePackageStripper(package)
    return stripper.visit(el)
