from __future__ import annotations

from quartodoc import layout
from plum import dispatch

from .utils import PydanticTransformer, ctx_node


# Visitor ---------------------------------------------------------------------


class CollectTransformer(PydanticTransformer):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.items: list[layout.Item] = []
        self.pages: list[layout.Page] = []

    def find_page_node(self):
        crnt_node = orig_node = ctx_node.get()  # noqa

        is_parent = False

        while is_parent is False:
            if crnt_node.value is None:
                raise ValueError(
                    f"No page detected above current element: {crnt_node.value}"
                )

            if isinstance(crnt_node.value, layout.Page):
                return crnt_node

            crnt_node = crnt_node.parent

        return crnt_node

    @dispatch
    def exit(self, el: layout.Doc):
        page_node = self.find_page_node()
        p_el = page_node.value

        anchor = el.name
        uri = f"{self.base_dir}/{p_el.path}.html#{anchor}"
        self.items.append(
            layout.Item(name=el.obj.path, obj=el.obj, uri=uri, dispname=None)
        )

        return el

    @dispatch
    def exit(self, el: layout.Page):
        self.pages.append(el)

        return el
