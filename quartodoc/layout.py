from __future__ import annotations

import griffe.dataclasses as dc
import logging

from pydantic import BaseModel, Field
from plum import dispatch

from typing import Any, Annotated, Literal, Union


_log = logging.getLogger(__name__)


class _Base(BaseModel):
    ...


class Layout(_Base):
    """The layout of an API doc, which may include many pages."""

    sections: list[SubElement | Section]


# SubElements -----------------------------------------------------------------


class Section(_Base):
    """Generic marker for a section of content."""

    kind: Literal["section"] = "section"
    title: str
    desc: str
    contents: list[SubElement | str]


class Page(_Base):
    kind: Literal["page"] = "page"
    path: str | None = None
    package: str | None = None
    name: str | None = None
    desc: str | None = None
    flatten: bool = False
    contents: list[SubElement | str]


class Text(_Base):
    kind: Literal["text"] = "text"
    contents: str


SubElement = Annotated[Union[Section, Page, Text], Field(discriminator="kind")]


# Update forwared refs --------------------------------------------------------

Layout.update_forward_refs()
Section.update_forward_refs()
Page.update_forward_refs()


# Visitor ---------------------------------------------------------------------


class Node(BaseModel):
    value: Any
    parent: Any = None

    def add(self, new_parent: BaseModel):
        return self.__class__(value=new_parent, parent=self)


class PydanticVisitor:
    @dispatch
    def visit(self, el: BaseModel, parent: Node):
        for field, value in el:
            self.visit(value, parent.add(el))

    @dispatch
    def visit(self, el: Union[list, tuple], parent: Node):
        for child in el:
            self.visit(child, parent.add(el))

    @dispatch
    def visit(self, el: BaseModel, parent: None = None):
        return self.visit(el, Node(value=None, parent=None))


class Item(BaseModel):
    obj: dc.Object | dc.Alias
    uri: str | None = None
    dispname: str | None = None

    class Config:
        arbitrary_types_allowed = True


class ItemCollector(PydanticVisitor):
    def __init__(self, get_object, base_dir: str, package: str, display_name: str):
        self.get_object = get_object
        self.base_dir = base_dir
        self.package = package
        self.display_name = display_name
        self.results: list[Item] = []

    def fetch_object_dispname(self, obj):
        """Define the name that will be displayed for individual api functions."""

        if self.display_name == "name":
            return obj.name
        elif self.display_name == "relative":
            return ".".join(obj.path.split(".")[1:])

        elif self.display_name == "full":
            return obj.path

        elif self.display_name == "canonical":
            return obj.canonical_path

        raise ValueError(f"Unsupported display_name: `{self.display_name}`")

    def _fetch_object(self, package, func_name):
        _log.info(f"Getting object for `{self.package}.{func_name}`")
        return self.get_object(package, func_name)

    @dispatch
    def visit(self, el: Section, parent: Node):
        for child in el.contents:
            if isinstance(child, str):
                obj = self._fetch_object(self.package, child)
                self.results.append(Item(obj=obj, uri=None, dispname=None))
            else:
                self.visit(child, parent.add(el))

    @dispatch
    def visit(self, el: Page, parent: Node):
        for child in el.contents:
            if isinstance(child, str):
                obj = self._fetch_object(self.package, child)
                anchor = self.fetch_object_dispname(obj)
                uri = f"{self.base_dir}/{el.path}#{anchor}"
                self.results.append(Item(obj=obj, uri=uri, dispname=None))
            else:
                self.visit(child, parent.add(el))

    @dispatch
    def visit(self, el: Text, parent: Node):
        pass
