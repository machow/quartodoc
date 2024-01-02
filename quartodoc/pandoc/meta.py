"""
Specifition is at https://pandoc.org/lua-filters.html#meta
"""
from __future__ import annotations

import yaml
from dataclasses import dataclass
from typing import Any

from .blocks import Block


@dataclass
class Meta(Block):
    """
    Pandoc meta data block
    """

    table: dict[str, Any]

    def __str__(self):
        yml = yaml.dump(self.table, allow_unicode=True, sort_keys=False)
        return f"---\n{yml}---"
