from __future__ import annotations

# NOTE:
# beartype is a runtime type checker and cannot properly handle
# type aliases defined using forward-references.
# --
# To avoid forward-references, these imported aliases are defined
# in the respective modules outside any typing.TYPE_CHECKING conditions.
# and when the objects they use have also been defined.
# --
# When using they they should be imported *outside* the
# typing.TYPE_CHECKING condition
from quartodoc.pandoc.blocks import BlockContent, DefinitionItem
from quartodoc.pandoc.inlines import InlineContent
