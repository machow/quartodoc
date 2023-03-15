from __future__ import annotations

import griffe.dataclasses as dc
import logging

from enum import Enum
from pydantic import BaseModel, Field

from typing import Annotated, Literal, Union


_log = logging.getLogger(__name__)


class _Base(BaseModel):
    ...


class Layout(_Base):
    """The layout of an API doc, which may include many pages."""

    sections: list[SectionElement | Section]
    package: str | None = None


# SubElements -----------------------------------------------------------------


class Section(_Base):
    """Generic marker for a section of content."""

    kind: Literal["section"] = "section"
    title: str
    desc: str
    contents: list[ContentElement | Doc | _AutoDefault]


class SummaryDetails(_Base):
    """Details that can be used in a summary table (e.g. on the index page)."""

    name: str
    desc: str = ""


class Page(_Base):
    """A page of documentation."""

    kind: Literal["page"] = "page"
    path: str | None = None
    package: str | None = None
    summary: SummaryDetails | None = None
    flatten: bool = False

    contents: list[ContentElement | Doc | _AutoDefault]

    @property
    def obj(self):
        # TODO: this is for the case where pages are put as members inside
        # a ClassDoc or ModuleDoc. We should use a different class for this.
        if len(self.contents) == 1:
            return self.contents[0].obj
        raise ValueError(
            ".obj property assumes contents field is length 1,"
            f" but it is {len(self.contents)}"
        )


class MemberPage(Page):
    """A page created as a result of documenting a member on a class or module."""

    contents: list[Doc]


class Text(_Base):
    kind: Literal["text"] = "text"
    contents: str


class ChoicesChildren(Enum):
    embedded = "embedded"
    flat = "flat"
    separate = "separate"


class Auto(_Base):
    kind: Literal["auto"] = "auto"
    name: str
    members: list[str] | None = None
    include_private: bool = False
    include: str | None = None
    exclude: str | None = None
    children: ChoicesChildren = ChoicesChildren.embedded


# TODO: rename to Default or something
class _AutoDefault(_Base):
    """This hacky class allows creating Auto as a default option in Pages and Sections."""

    __root__: str | dict

    def __new__(cls, __root__: str | dict):
        if isinstance(__root__, dict):
            return Auto(**__root__)

        return Auto(name=__root__)


class Link(_Base):
    """A link to an object (e.g. a method that gets documented on a separate page)."""

    name: str
    obj: dc.Object | dc.Alias

    class Config:
        arbitrary_types_allowed = True


class Doc(_Base):
    name: str
    obj: dc.Object | dc.Alias
    anchor: str

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_griffe(cls, obj: dc.Object | dc.Alias, members=None, anchor: str = None):
        if members is None:
            members = []

        kind = obj.kind.value
        anchor = obj.path if anchor is None else anchor

        kwargs = {"obj": obj, "anchor": anchor}

        if kind == "function":
            return DocFunction(name=obj.path, **kwargs)
        elif kind == "attribute":
            return DocAttribute(name=obj.path, **kwargs)
        elif kind == "class":
            return DocClass(name=obj.path, members=members, **kwargs)
        elif kind == "module":
            return DocModule(name=obj.path, members=members, **kwargs)

        raise TypeError(f"Cannot handle auto for object kind: {obj.kind}")


class DocFunction(Doc):
    kind: Literal["function"] = "function"


class DocClass(Doc):
    kind: Literal["class"] = "class"
    members: list[MemberPage | Link | Doc] = tuple()


class DocAttribute(Doc):
    kind: Literal["attribute"] = "attribute"


class DocModule(Doc):
    kind: Literal["module"] = "module"
    members: list[MemberPage | Link | Doc] = tuple()


SectionElement = Annotated[Union[Section, Page], Field(discriminator="kind")]
ContentElement = Annotated[Union[Page, Text, Auto], Field(discriminator="kind")]

# Item ----


class Item(BaseModel):
    name: str
    obj: dc.Object | dc.Alias
    uri: str | None = None
    dispname: str | None = None

    class Config:
        arbitrary_types_allowed = True


# Update forwared refs --------------------------------------------------------

Layout.update_forward_refs()
Section.update_forward_refs()
Page.update_forward_refs()
Auto.update_forward_refs()
