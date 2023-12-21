"""
Specifition is at https://pandoc.org/lua-filters.html#inline
"""
from __future__ import annotations

import collections.abc as abc
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = "TypeAlias"

from quartodoc.pandoc.components import Attr

__all__ = (
    "Code",
    "Emph",
    "Image",
    "Inline",
    "Inlines",
    "Link",
    "Span",
    "Str",
    "Strong",
)

SEP = " "


class Inline:
    """
    Base class for inline elements
    """

    def __str__(self):
        """
        Return Inline element as markdown
        """
        raise NotImplementedError(f"__str__ method not implemented for: {type(self)}")

    @property
    def html(self):
        """
        Return Inline element as HTML code

        This method is useful for cases where markdown is not versatile
        enough for a specific outcome.
        """
        raise NotImplementedError(
            f"html property method not implemented for: {type(self)}"
        )

    @property
    def as_list_item(self):
        """
        An inline as a list item
        """
        return str_as_list_item(str(self))


# TypeAlias declared here to avoid forward-references which
# break beartype
InlineContentItem = Union[str, Inline, None]
InlineContent: TypeAlias = Union[InlineContentItem, Sequence[InlineContentItem]]


@dataclass
class Inlines(Inline):
    """
    Sequence of inline elements
    """

    elements: Optional[Sequence[InlineContent]] = None

    def __str__(self):
        if not self.elements:
            return ""
        return join_inline_content(self.elements)


@dataclass
class Str(Inline):
    """
    A String
    """

    content: Optional[str] = None

    def __str__(self):
        return self.content or ""


@dataclass
class Span(Inline):
    """
    A Span
    """

    content: Optional[InlineContent] = None
    attr: Optional[Attr] = None

    def __str__(self):
        """
        Return span content as markdown
        """
        content = inlinecontent_to_str(self.content)
        attr = self.attr or ""
        return f"[{content}]{{{attr}}}"


@dataclass
class Link(Inline):
    """
    A Link
    """

    content: Optional[InlineContent] = None
    target: Optional[str] = None
    title: Optional[str] = None
    attr: Optional[Attr] = None

    def __str__(self):
        """
        Return link as markdown
        """
        title = f' "{self.title}"' if self.title else ""
        content = inlinecontent_to_str(self.content)
        attr = f"{{{self.attr}}}" if self.attr else ""
        return f"[{content}]({self.target}{title}){attr}"


@dataclass
class Code(Inline):
    """
    Code (inline)
    """

    text: Optional[str] = None
    attr: Optional[Attr] = None

    def __str__(self):
        """
        Return link as markdown
        """
        content = self.text or ""
        attr = f"{{{self.attr}}}" if self.attr else ""
        return f"`{content}`{attr}"

    @property
    def html(self):
        """
        Code (inline) rendered as html

        Notes
        -----
        Generates html as if the `--no-highlight` option as passed
        to pandoc
        """
        content = self.text or ""
        attr = f" {self.attr.html}" if self.attr else ""
        return f"<code{attr}>{content}</code>"


@dataclass
class Strong(Inline):
    """
    Strongly emphasized text
    """

    content: Optional[InlineContent] = None

    def __str__(self):
        """
        Return link as markdown
        """
        if not self.content:
            return ""

        content = inlinecontent_to_str(self.content)
        return f"**{content}**"


@dataclass
class Emph(Inline):
    """
    Emphasized text
    """

    content: Optional[InlineContent] = None

    def __str__(self):
        """
        Return link as markdown
        """
        if not self.content:
            return ""

        content = inlinecontent_to_str(self.content)
        return f"*{content}*"


@dataclass
class Image(Inline):
    """
    Image
    """

    caption: Optional[str] = None
    src: Optional[Path | str] = None
    title: Optional[str] = None
    attr: Optional[Attr] = None

    def __str__(self):
        """
        Return image as markdown
        """
        caption = self.caption or ""
        src = self.src or ""
        title = f' "{self.title}"' if self.title else ""
        attr = f"{{{self.attr}}}" if self.attr else ""
        return f"![{caption}]({src}{title}){attr}"


# Helper functions


def join_inline_content(content: Sequence[InlineContent]) -> str:
    """
    Join a sequence of inlines into one string
    """
    return SEP.join(inlinecontent_to_str(c) for c in content if c)


def inlinecontent_to_str(content: Optional[InlineContent]):
    """
    Covert inline content to a string

    A single item block is converted to a string.
    A block sequence is coverted to a string of strings with a
    space separating the string for each item in the sequence.
    """
    if not content:
        return ""
    elif isinstance(content, (str, Inline)):
        return str(content)
    elif isinstance(content, abc.Sequence):
        return join_inline_content(content)
    else:
        raise TypeError(f"Could not process type: {type(content)}")


def str_as_list_item(s: str) -> str:
    """
    How a string becomes a list item
    """
    return f"{s}\n"
