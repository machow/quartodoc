from __future__ import annotations

from ._griffe_compat import dataclasses as dc
import logging

from enum import Enum
from typing_extensions import Annotated
from typing import Literal, Union, Optional

from ._pydantic_compat import BaseModel, Field, Extra, PrivateAttr


_log = logging.getLogger(__name__)


class _Base(BaseModel):
    """Any data class that might appear in the quartodoc config."""

    class Config:
        extra = Extra.forbid


class _Structural(_Base):
    """A structural element, like an index Section or Page of docs."""


class _Docable(_Base):
    """An element meant to document something about a python object."""


class MISSING(_Base):
    """Represents a missing value.

    Note that this is used in cases where None is meaningful.
    """


class Layout(_Structural):
    """The layout of an API doc, which may include many pages.

    Attributes
    ----------
    sections:
        Top-level sections of the quarto layout config.
    package:
        The package being documented.
    """

    sections: list[Union[SectionElement, Section]] = []
    package: Union[str, None, MISSING] = MISSING()
    options: Optional["AutoOptions"] = None


# SubElements -----------------------------------------------------------------


class Section(_Structural):
    """A section of content on the reference index page.

    Attributes
    ----------
    kind:
    title:
        Title of the section on the index.
    subtitle:
        Subtitle of the section on the index. Note that either title or subtitle,
        but not both, may be set.
    desc:
        Description of the section on the index.
    package:
        If specified, all object lookups will be relative to this path.
    contents:
        Individual objects (e.g. functions, classes, methods) being documented.
    """

    kind: Literal["section"] = "section"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    desc: Optional[str] = None
    package: Union[str, None, MISSING] = MISSING()
    contents: ContentList = []
    options: Optional["AutoOptions"] = None

    def __init__(self, **data):
        super().__init__(**data)

        # TODO: should these be a custom type? Or can we use pydantic's ValidationError?
        if self.title is None and self.subtitle is None and not self.contents:
            raise ValueError(
                "Section must specify a title, subtitle, or contents field"
            )
        elif self.title is not None and self.subtitle is not None:
            raise ValueError("Section cannot specify both title and subtitle fields.")


class SummaryDetails(_Base):
    """Details that can be used in a summary table (e.g. on the index page)."""

    name: str
    desc: str = ""


class Page(_Structural):
    """A page of documentation.

    Attributes
    ----------
    kind:
    path:
        The file path this page should be written to (without an extension).
    package:
        If specified, all object lookups will be relative to this path.
    summary:
        An optional title and description for the page.
    flatten:
        Whether to list out each object on this page in the index.
    """

    kind: Literal["page"] = "page"
    path: str
    package: Union[str, None, MISSING] = MISSING()
    summary: Optional[SummaryDetails] = None
    flatten: bool = False

    contents: ContentList

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


class Interlaced(_Docable):
    """A group of objects, whose documentation will be interlaced.

    Rather than list each object's documentation in sequence, this element indicates
    that each piece of documentation (e.g. signatures, examples) should be grouped
    together.

    Attributes
    ----------
    kind:
    package:
        If specified, all object lookups will be relative to this path.

    """

    kind: Literal["interlaced"] = "interlaced"
    package: Union[str, None, MISSING] = MISSING()

    # note that this is similar to a ContentList, except it cannot include
    # elements like Pages, etc..
    contents: list[Union[Auto, Doc, _AutoDefault]]

    @property
    def name(self):
        if not self.contents:
            raise AttributeError(
                f"Cannot get property name for object of type {type(self)}."
                " There are no content elements."
            )

        return self.contents[0].name


class Text(_Docable):
    kind: Literal["text"] = "text"
    contents: str


class ChoicesChildren(Enum):
    """Options for how child members of a class or module should be documented.

    Attributes
    ----------
    embedded:
        Embed documentation inside the parent object's documentation.
    flat:
        Include documentation after the parent object's documentation.
    separate:
        Put documentation for members on their own, separate pages.
    linked:
        Include only a table of links to members (which may not be documented).
    """

    embedded = "embedded"
    flat = "flat"
    separate = "separate"
    linked = "linked"


SignatureOptions = Literal["full", "short", "relative"]


class AutoOptions(_Base):
    """Options available for Auto content layout element."""

    signature_name: SignatureOptions = "relative"
    members: Optional[list[str]] = None
    include_private: bool = False
    include_imports: bool = False
    include_empty: bool = False
    include_inherited: bool = False

    # member types to include ----
    include_attributes: bool = True
    include_classes: bool = True
    include_functions: bool = True

    # other options ----
    include: Optional[str] = None
    exclude: Optional[list[str]] = None
    dynamic: Union[None, bool, str] = None
    children: ChoicesChildren = ChoicesChildren.embedded
    package: Union[str, None, MISSING] = MISSING()
    member_order: Literal["alphabetical", "source"] = "alphabetical"
    member_options: Optional["AutoOptions"] = None

    # for tracking fields users manually specify
    # so we can tell them apart from defaults
    _fields_specified: list[str] = PrivateAttr(default=())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._fields_specified = tuple(kwargs)


class Auto(AutoOptions):
    """Configure a python object to document (e.g. module, class, function, attribute).

    Attributes
    ----------
    name:
        Name of the object. This should be the path needed to import it.
    signature_name:
        Style of name to use in the signature. Can be "relative", "full", or "short".
        Relative is whatever was used as the name argument, full is the fully qualified
        path the object, and short is the name of the object (i.e. no periods).
    members:
        A list of members, such as attributes or methods on a class, to document.
        If members is specified, no other includes or excludes are applied.
    include_private:
        Whether to include members starting with "_"
    include_imports:
        Whether to include members that were imported from somewhere else.
    include_empty:
        Whether to include members with no docstring.
    include_inherited:
        Whether to include members inherited from a parent class.
    include_attributes:
        Whether to include attributes.
    include_classes:
        Whether to include classes.
    include_functions:
        Whether to include functions.
    include:
        (Not implemented). A list of members to include.
    exclude:
        A list of members to exclude. This is performed last, in order to subtract
        from the results of options like include_functions.
    dynamic:
        Whether to dynamically load docstring. By default docstrings are loaded
        using static analysis. dynamic may be a string pointing to another object,
        to return an alias for that object.
    children:
        Style for presenting members. Either separate, embedded, or flat.
    package:
        If specified, object lookup will be relative to this path.
    member_order:
        Order to present members in, either "alphabetical" or "source" order.
        Defaults to alphabetical sorting.
    member_options:
        Options to apply to members. These can include any of the options above.

    """

    kind: Literal["auto"] = "auto"
    name: str


# TODO: rename to Default or something
class _AutoDefault(_Base):
    """This hacky class allows creating Auto as a default option in Pages and Sections."""

    __root__: Union[str, dict]

    def __new__(cls, __root__: Union[str, dict]):
        if isinstance(__root__, dict):
            return Auto(**__root__)

        return Auto(name=__root__)


class Link(_Docable):
    """A link to an object (e.g. a method that gets documented on a separate page).

    Link can be thought of as an alternative to [](`quartodoc.layout.Doc`). It doesn't
    represent the documenting of an object, but a link to be made to some documentation.
    """

    name: str
    obj: Union[dc.Object, dc.Alias]

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid


class Doc(_Docable):
    """A python object to be documented.

    Note that this class should not be used directly. Instead, use child classes
    like DocFunction.

    Attributes
    ----------
    name:
        The import path of the object (e.g. quartodoc.get_object).
    obj:
        The loaded python object.
    anchor:
        An anchor named, used to locate this documentation on a [](`quartodoc.layout.Page`).

    See Also
    --------
    [](`quartodoc.layout.DocModule`), [](`quartodoc.layout.DocClass`),
    [](`quartodoc.layout.DocFunction`), [](`quartodoc.layout.DocAttribute`)

    """

    name: str
    obj: Union[dc.Object, dc.Alias]
    anchor: str
    signature_name: SignatureOptions = "relative"

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid

    @classmethod
    def from_griffe(
        cls,
        name,
        obj: Union[dc.Object, dc.Alias],
        members=None,
        anchor: str = None,
        flat: bool = False,
        signature_name: str = "relative",
    ):
        if members is None:
            members = []

        kind = obj.kind.value
        anchor = obj.path if anchor is None else anchor

        kwargs = {
            "name": name,
            "obj": obj,
            "anchor": anchor,
            "signature_name": signature_name,
        }

        if kind == "function":
            return DocFunction(**kwargs)
        elif kind == "attribute":
            return DocAttribute(**kwargs)
        elif kind == "class":
            return DocClass(members=members, flat=flat, **kwargs)
        elif kind == "module":
            return DocModule(members=members, flat=flat, **kwargs)

        raise TypeError(f"Cannot handle auto for object kind: {obj.kind}")


class DocFunction(Doc):
    """Document a python function."""

    kind: Literal["function"] = "function"


class DocClass(Doc):
    """Document a python class."""

    kind: Literal["class"] = "class"
    members: list[Union[MemberPage, Doc, Link]] = tuple()
    flat: bool


class DocAttribute(Doc):
    """Document a python attribute."""

    kind: Literal["attribute"] = "attribute"


class DocModule(Doc):
    """Document a python module."""

    kind: Literal["module"] = "module"
    members: list[Union[MemberPage, Doc, Link]] = tuple()
    flat: bool


SectionElement = Annotated[Union[Section, Page], Field(discriminator="kind")]
"""Entry in the sections list."""

ContentElement = Annotated[
    Union[Page, Section, Interlaced, Text, Auto], Field(discriminator="kind")
]
"""Entry in the contents list."""

ContentList = list[Union[_AutoDefault, ContentElement, Doc]]

# Item ----


class Item(BaseModel):
    """Information about a documented object, including a URI to its location.

    Item is used to creative relative links within a documented API. All of the
    items for an API are saved as an inventory file (usually named objects.json),
    so documentation sites can link across each other.

    Attributes
    ----------
    name:
        The name of the object.
    obj:
        A representation of the object (eg its parameters and parsed docstring)
    uri:
        A relative URI link to the object from the root of the documentation site.
    dispname:
        Default display name, if none is specified in the interlink. If None, the
        default is to dipslay the name attribute.

    """

    name: str
    obj: Union[dc.Object, dc.Alias]
    uri: Optional[str] = None
    dispname: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid


# Update forwared refs --------------------------------------------------------

Layout.update_forward_refs()
Section.update_forward_refs()
Page.update_forward_refs()
AutoOptions.update_forward_refs()
Auto.update_forward_refs()
MemberPage.update_forward_refs()
Interlaced.update_forward_refs()
