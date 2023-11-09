"""
Specifition is at https://pandoc.org/lua-filters.html#block
"""
from __future__ import annotations

import itertools
import typing
from typing import Literal, Optional, TypeAlias, Sequence
import collections.abc as abc

from textwrap import indent
from dataclasses import dataclass

from quartodoc.pandoc.components import Attr
from quartodoc.pandoc.inlines import Inline, Inlines, InlineContent, inlinecontent_to_str

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
        raise NotImplementedError(
            f"__str__ method not implemented for: {type(self)}"
        )

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


# TypeAlias declared here to avoid forward-references which
# break beartype
BlockContent: TypeAlias = InlineContent | Block | Sequence[Block]
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
:::
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


# Description starts on the 4th column, and subsequent lines will be
# indented with 4 spaces. This is crucial for proper handling of
# descriptions with more than one block.
DefinitionItem_TPL = """\
{term}
:   {description}
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

        lst = []
        fmt = DefinitionItem_TPL.format
        for term, description in self.content:
            term = inlinecontent_to_str(term)
            description = blockcontent_to_str(description)

            # strip away the indentation on the first line as it
            # is handled by the template
            desc = indent(str(description).strip(), INDENT).strip()
            lst.append(fmt(term=term, description=desc))

        return join_block_content(lst)


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


CodeBlock_TPL = """
```{attr}
{content}
```
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
                self.attr.classes and
                len(self.attr.classes) == 1 and
                not self.attr.attributes
            )

            if self.attr.classes and no_curly_braces:
                attr = self.attr.classes[0]
            else:
                attr = f" {{{self.attr}}}"
        else:
            attr = ""

        return CodeBlock_TPL.format(content=content, attr=attr)


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
    return f"{SEP}{SEP}".join(str(c).rstrip(SEP) for c in content if c)


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
        return str(content)
    elif isinstance(content, abc.Sequence):
        return join_block_content(content)
    else:
        raise TypeError(f"Could not process type: {type(content)}")


def blockcontent_to_str_items(
    content: Optional[BlockContent],
    kind: Literal["bullet", "ordered"]
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

    def fmt(s:str, pfx: str):
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
        pad = " " * (len(pfx) + 1)
        return f"{pfx} " + indent(s, pad).lstrip(pad)

    if not content:
        return ""

    if kind == "bullet":
        pfx_it  = itertools.cycle("*")
    else:
        pfx_it = (f"{i}." for i in itertools.count(1))

    if isinstance(content, (str, Inline, Block)):
        return fmt(str(content), next(pfx_it))
    elif isinstance(content, abc.Sequence):
        # To balance correctness, compactness and readability,
        # items with content get an empty line between them and
        # the next item.
        items = []
        pad = ""
        for item in content:
            s = fmt(str(item), next(pfx_it))
            pad = f"{SEP}{SEP}" if isinstance(item, Block) else f"{SEP}"
            items.append(f"{s}{pad}")
        return "".join(items)[:-len(pad)]
    else:
        raise TypeError(f"Could not process type: {type(content)}")
