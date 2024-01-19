"""
Specifition is at https://pandoc.org/lua-filters.html#block
"""
from __future__ import annotations

import collections.abc as abc
import itertools
import sys

from textwrap import indent
from dataclasses import dataclass
from typing import Literal, Optional, Sequence, Union

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = "TypeAlias"

from quartodoc.pandoc.components import Attr
from quartodoc.pandoc.inlines import (
    Inline,
    InlineContent,
    InlineContentItem,
    inlinecontent_to_str,
    str_as_list_item,
)

__all__ = (
    "Block",
    "Blocks",
    "BulletList",
    "CodeBlock",
    "DefinitionList",
    "Div",
    "Header",
    "OrderedList",
    "Para",
    "Plain",
)

INDENT = " " * 4
SEP = "\n"


class Block:
    """
    Base class for block elements
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
        A block as a list item

        Some block type need special spacing consideration
        """
        # To balance correctness, compactness and readability,
        # block items get an empty line between them and the next
        # item.
        return f"{self}\n\n"


# TypeAlias declared here to avoid forward-references which
# break beartype
BlockContentItem: TypeAlias = Union[InlineContentItem, Block]
BlockContent: TypeAlias = Union[BlockContentItem, Sequence[BlockContentItem]]
DefinitionItem: TypeAlias = tuple[InlineContent, BlockContent]


@dataclass
class Blocks(Block):
    elements: Optional[Sequence[BlockContent]] = None

    def __str__(self):
        if not self.elements:
            return ""
        return join_block_content(self.elements)


Div_TPL = """\
::: {{{attr}}}
{content}
:::\
"""


@dataclass
class Div(Block):
    """
    A Div
    """

    content: Optional[BlockContent] = None
    attr: Optional[Attr] = None

    def __str__(self):
        """
        Return div content as markdown
        """
        content = blockcontent_to_str(self.content)
        attr = self.attr or ""
        return Div_TPL.format(content=content, attr=attr)


# Definition starts on the 4th column, and subsequent lines will be
# indented with 4 spaces. This is crucial for proper handling of
# definition with more than one block.
DefinitionItem_TPL = """\
{term}
{definitions}\
"""

Definition_TPL = """
:   {definition}
"""


@dataclass
class DefinitionList(Block):
    """
    A definition list
    """

    content: Optional[Sequence[DefinitionItem]] = None

    def __str__(self):
        """
        Return definition list as markdown
        """
        if not self.content:
            return ""

        tfmt = DefinitionItem_TPL.format
        dfmt = Definition_TPL.format
        items = []
        for term, definitions in self.content:
            term, defs = inlinecontent_to_str(term), []

            # Single Definition
            if isinstance(definitions, (str, Inline, Block)):
                definitions = [definitions]
            elif definitions is None:
                definitions = [""]

            # Multiple definitions
            for definition in definitions:
                s = blockcontent_to_str(definition)
                # strip away the indentation on the first line as it
                # is handled by the template
                defs.append(dfmt(definition=indent(s, INDENT).strip()))

            items.append(tfmt(term=term, definitions="".join(defs)))

        return join_block_content(items)


@dataclass
class Plain(Block):
    """
    Plain text (not a paragraph)
    """

    content: Optional[InlineContent] = None

    def __str__(self):
        return inlinecontent_to_str(self.content)


@dataclass
class Para(Block):
    """
    Paragraph
    """

    content: Optional[InlineContent] = None

    def __str__(self):
        content = inlinecontent_to_str(self.content)
        return f"{SEP}{content}{SEP}"

    @property
    def as_list_item(self):
        content = inlinecontent_to_str(self.content)
        return f"{content}\n\n"


@dataclass
class Header(Block):
    """
    Header
    """

    level: int
    content: Optional[InlineContent] = None
    attr: Optional[Attr] = None

    def __str__(self):
        hashes = "#" * self.level
        content = inlinecontent_to_str(self.content)
        attr = f" {{{self.attr}}}" if self.attr else ""
        return f"{hashes} {content}{attr}"


CodeBlock_TPL = """\
```{attr}
{content}
```\
"""
CodeBlockHTML_TPL = """\
<pre{attr}>
<code>{content}</code>
</pre>\
"""


@dataclass
class CodeBlock(Block):
    """
    Header
    """

    content: Optional[str] = None
    attr: Optional[Attr] = None

    def __str__(self):
        content = self.content or ""
        if self.attr:
            # When the code block has a single class and no
            # other attributes, use a short form to open it
            # e.g. ```python instead of ``` {.python}
            no_curly_braces = (
                self.attr.classes
                and len(self.attr.classes) == 1
                and not self.attr.attributes
            )

            if self.attr.classes and no_curly_braces:
                attr = self.attr.classes[0]
            else:
                attr = f" {{{self.attr}}}"
        else:
            attr = ""

        return CodeBlock_TPL.format(content=content, attr=attr)

    @property
    def html(self):
        """
        Code (block) rendered as html

        Notes
        -----
        Generates html as if the `--no-highlight` option as passed
        to pandoc
        """
        content = self.content or ""
        attr = f" {self.attr.html}" if self.attr else ""
        return CodeBlockHTML_TPL.format(content=content, attr=attr)

    @property
    def as_list_item(self):
        return f"\n{self}\n\n"


@dataclass
class BulletList(Block):
    """
    A bullet list
    """

    content: Optional[BlockContent] = None

    def __str__(self):
        """
        Return a bullet list as markdown
        """
        if not self.content:
            return ""
        return blockcontent_to_str_items(self.content, "bullet")


@dataclass
class OrderedList(Block):
    """
    An Ordered list
    """

    content: Optional[BlockContent] = None

    def __str__(self):
        """
        Return an ordered list as markdown
        """
        if not self.content:
            return ""
        return blockcontent_to_str_items(self.content, "ordered")


# Helper functions


def join_block_content(content: Sequence[BlockContent]) -> str:
    """
    Join a sequence of blocks into one string
    """
    # Ensure that there are exactly two newlines (i.e. one empty line)
    # between any items.
    return f"{SEP}{SEP}".join(blockcontent_to_str(c) for c in content if c)


def blockcontent_to_str(content: Optional[BlockContent]) -> str:
    """
    Covert block content to a string

    A single item block is converted to a string.
    A block sequence is coverted to a string of strings with a
    newline separating the string for each item in the sequence.
    """
    if not content:
        return ""
    elif isinstance(content, (str, Inline, Block)):
        return str(content).rstrip(SEP)
    elif isinstance(content, abc.Sequence):
        return join_block_content(content)
    else:
        raise TypeError(f"Could not process type: {type(content)}")


def blockcontent_to_str_items(
    content: Optional[BlockContent], kind: Literal["bullet", "ordered"]
) -> str:
    """
    Convert block content to strings of items

    Parameters
    ----------
    content:
        What to convert

    kind:
        How to mark (prefix) each item in the of content.
    """

    def fmt(s: str, pfx: str):
        """
        Format as a list item with one or more blocks
        """
        # Aligns the content in all lines to start in the same column.
        # e.g. If pfx = "12.", we get output like
        #
        # 12. abcd
        #     efgh
        #
        #     ijkl
        #     mnop
        if not s:
            return ""

        # We avoid having a space after the item bullet/number if
        # there is no content on that line
        space = ""
        indent_size = len(pfx) + 1
        s_indented = indent(s, " " * indent_size)
        if s[0] != "\n":
            space = " "
            s_indented = s_indented[indent_size:]
        return f"{pfx}{space}{s_indented}"

    if not content:
        return ""

    if kind == "bullet":
        pfx_it = itertools.cycle("*")
    else:
        pfx_it = (f"{i}." for i in itertools.count(1))

    if isinstance(content, str):
        return fmt(str_as_list_item(content), next(pfx_it))
    elif isinstance(content, (Inline, Block)):
        return fmt(content.as_list_item, next(pfx_it))
    elif isinstance(content, abc.Sequence):
        it = (
            str_as_list_item(c) if isinstance(c, str) else c.as_list_item
            for c in content
            if c
        )
        items = (fmt(s, next(pfx_it)) for s in it)
        return "".join(items).strip()
    else:
        raise TypeError(f"Could not process type: {type(content)}")
