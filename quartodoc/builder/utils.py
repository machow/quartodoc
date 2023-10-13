from __future__ import annotations

from contextvars import ContextVar
from plum import dispatch
from typing import Union

from quartodoc._pydantic_compat import BaseModel
from ._node import Node


# Transformer -----------------------------------------------------------------

ctx_node: ContextVar[Node] = ContextVar("node")


class WorkaroundKeyError(Exception):
    """Represents a KeyError.

    Note that this is necessary to work around a bug in plum dispatch, which
    intercepts KeyErrors, and then causes an infinite recursion by re-calling
    the dispatcher.
    """


class PydanticTransformer:
    LOG = False

    def _log(self, step: str, el):
        if self.LOG:
            print(f"{step}: {type(el)} {el}")

    @dispatch
    def visit(self, el):
        self._log("PARENT VISITING", el)

        old_node = ctx_node.get(None)
        if old_node is None:
            old_node = Node()

        new_node = Node(level=old_node.level + 1, value=el, parent=old_node)

        token = ctx_node.set(new_node)

        try:
            result = self.enter(el)
            return self.exit(result)
        finally:
            ctx_node.reset(token)

    @dispatch
    def enter(self, el):
        self._log("GENERIC ENTER", el)
        return el

    @dispatch
    def exit(self, el):
        self._log("GENERIC EXIT", el)
        return el

    @dispatch
    def enter(self, el: BaseModel):
        self._log("GENERIC ENTER", el)
        new_kwargs = {}

        has_change = False
        for field, value in el:
            result = self.visit(value)
            if result is not value:
                has_change = True
                new_kwargs[field] = result
            else:
                new_kwargs[field] = value

        if has_change:
            return el.__class__(**new_kwargs)

        return el

    @dispatch
    def enter(self, el: Union[list, tuple]):
        self._log("GENERIC ENTER", el)
        final = []

        # has_change = False
        for child in el:
            result = self.visit(child)
            if result is not child:
                # has_change = True
                final.append(result)
            else:
                final.append(child)

        # for now just return a copy always
        return el.__class__(final)


# Implementations -------------------------------------------------------------


class _TypeExtractor(PydanticTransformer):
    def __init__(self, target_cls):
        self.target_cls = target_cls
        self.results = []

    @dispatch
    def exit(self, el):
        if isinstance(el, self.target_cls):
            self.results.append(el)

        return el

    @classmethod
    def run(cls, target_cls, el):
        extractor = cls(target_cls)
        extractor.visit(el)

        return extractor.results


extract_type = _TypeExtractor.run
