"""
Specification: https://pandoc.org/lua-filters.html#element-components-1
"""
from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import Optional, Sequence

__all__ = ("Attr",)


@dataclass
class Attr:
    """
    Create a new set of attributes (Attr)
    """

    identifier: Optional[str] = None
    classes: Optional[Sequence[str]] = None
    attributes: Optional[dict[str, str]] = None

    def __str__(self):
        """
        Return attr the contents of curly bracked attributes

        e.g.

            #id1 .class1 .class2 width="50%" height="50%"

        not

            {#id1 .class1 .class2 width="50%" height="50%"}
        """
        parts = []
        if self.identifier:
            parts.append(f"#{self.identifier}")

        if self.classes:
            parts.append(" ".join(f".{c}" for c in self.classes))

        if self.attributes:
            parts.append(" ".join(f'{k}="{v}"' for k, v in self.attributes.items()))

        return " ".join(parts)

    @property
    def html(self):
        """
        Represent Attr as it would appear in an HTML tag

        e.g.

            id="id1" class="class1 class2" width="50%" height="50%"
        """
        parts = []

        if self.identifier:
            parts.append(f'id="{self.identifier}"')

        if self.classes:
            s = " ".join(c for c in self.classes)
            parts.append(f'class="{s}"')

        if self.attributes:
            parts.append(" ".join(f'{k}="{v}"' for k, v in self.attributes.items()))
        return " ".join(parts)

    @property
    def empty(self) -> bool:
        """
        Return True if Attr has no content
        """
        return not (self.identifier or self.classes or self.attributes)
