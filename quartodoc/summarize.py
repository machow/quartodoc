from __future__ import annotations

import griffe.dataclasses as dc
import griffe.docstrings.dataclasses as ds

from plum import dispatch
from quartodoc import layout

from typing import Union


class ItemLookupError(Exception):
    """Represents a failed attempt to lookup an inventory item."""


class MdSummarizer:
    """Render tables with linked name and description for sections of objects."""

    def __init__(
        self, use_interlinks: bool = False, items: None | list[layout.Item] = None,
    ):

        if not use_interlinks and items is None:
            raise ValueError("Must specify use_interlinks=True or pass items.")

        self.use_interlinks = use_interlinks
        self.items = items or []
        self.item_map = {el.name: el for el in items}

    def fetch_object_link(self, el: dc.Object | dc.Alias):
        if self.use_interlinks:
            return f"[](`{el.path}`)"

        try:
            item = self.item_map[el.path]
            text = item.dispname or item.name
            return f"[{text}](/{item.uri})"

        except KeyError:
            raise ItemLookupError(f"No inventory item for object with path: {el.path}")

    @dispatch
    def summarize(self, el: layout.Layout):
        rendered_sections = list(map(self.summarize, el.sections))
        return "\n\n".join(rendered_sections)

    @dispatch
    def summarize(self, el: layout.Section):
        header = f"## {el.title}\n\n{el.desc}"

        thead = "| | |\n| --- | --- |"

        rendered = []
        for child in el.contents:
            rendered.append(self.summarize(child))

        str_func_table = "\n".join([thead, *rendered])
        return f"{header}\n\n{str_func_table}"

    @dispatch
    def summarize(self, el: layout.Page):
        if len(el.contents) > 1 and not el.flatten:
            if el.summary is not None:
                return f"| [{el.summary.name}]({el.path}) | {el.summary.desc} |"

            raise ValueError(
                "Cannot summarize Page. Either set its `summary` attribute with name "
                "and description details, or set `flatten` to True."
            )

        else:
            return "\n".join(list(map(self.summarize, el.contents)))

    @dispatch
    def summarize(self, el: layout.Doc):
        return self.summarize(el.obj)

    @dispatch
    def summarize(self, el: layout.Link):
        return self.summarize(el.obj)

    @dispatch
    def summarize(self, obj: Union[dc.Object, dc.Alias]):
        # get high-level description
        doc = obj.docstring
        if doc is None:
            # TODO: add a single empty
            docstring_parts = []
        else:
            docstring_parts = doc.parsed

        # TODO: look up from inventory?
        link = self.fetch_object_link(obj)
        if len(docstring_parts) and isinstance(
            docstring_parts[0], ds.DocstringSectionText
        ):
            # TODO: or canonical_path
            description = docstring_parts[0].value
            short = description.split("\n")[0]
            return f"| {link} | {short} |"
        else:
            return f"| {link} | |"
