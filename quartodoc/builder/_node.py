# Note: this class is in its own file to ensure compatibility with python 3.9.
# If it were in another file, then we would have to change all our types to
# use Union and Optional, or pyndantic would error.

from __future__ import annotations

from quartodoc._pydantic_compat import BaseModel
from typing import Any, Optional


class Node(BaseModel):
    level: int = -1
    value: Any = None
    parent: Optional[Node] = None


Node.update_forward_refs()
