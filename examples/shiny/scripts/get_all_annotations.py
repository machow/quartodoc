from __future__ import annotations

from quartodoc.builder.utils import PydanticTransformer
from pydantic import BaseModel
from plum import dispatch

import griffe.dataclasses as dc


class AnnotationFetcher(PydanticTransformer):
    def __init__(self):
        self.annotations = []

    @dispatch
    def exit(self, el: dc.Object | dc.Alias):
        if el.is_module or el.is_attribute:
            return el

        self.annotations.extend([x.annotation for x in el.parameters])

        return el


def get_annotations(el: BaseModel | dc.Object | dc.Alias):
    fetcher = AnnotationFetcher()
    fetcher.visit(el)

    return fetcher.annotations
