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

        uri = f"{self.base_dir}/{p_el.path}.html#{el.anchor}"

        name_path = el.obj.path
        canonical_path = el.obj.canonical_path

        # item corresponding to the specified path ----
        # e.g. this might be a top-level import
        self.items.append(
            layout.Item(name=name_path, obj=el.obj, uri=uri, dispname=None)
        )

        if name_path != canonical_path:
            # item corresponding to the canonical path ----
            # this is where the object is defined (which may be deep in a submodule)
            self.items.append(
                layout.Item(
                    name=canonical_path, obj=el.obj, uri=uri, dispname=name_path
                )
            )

        return el

    @dispatch
    def exit(self, el: layout.Page):
        self.pages.append(el)

        return el


def collect(el: layout._Base, base_dir: str):
    """Return all pages and items in a layout.

    Parameters
    ----------
    el:
        An element, like layout.Section or layout.Page, to collect pages and items from.
    base_dir:
        The directory where API pages will live.


    """

    trans = CollectTransformer(base_dir=base_dir)
    trans.visit(el)

    return trans.pages, trans.items
