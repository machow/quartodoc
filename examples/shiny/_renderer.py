from __future__ import annotations

import html
from importlib.resources import files
from quartodoc import MdRenderer
from quartodoc.renderers.base import convert_rst_link_to_md
from plum import dispatch
from typing import Union

from griffe import dataclasses as dc
from griffe.docstrings import dataclasses as ds


SHINY_PATH = files("shiny")

SHINYLIVE_TMPL = """
```{{shinylive-python}}
#| standalone: true

{0}
```
"""

DOCSTRING_TMPL = """\
{rendered}

Examples
--------

{examples}
"""


class Renderer(MdRenderer):
    style = "shiny"

    @dispatch
    def render(self, el: Union[dc.Object, dc.Alias]):
        rendered = super().render(el)

        converted = convert_rst_link_to_md(rendered)

        p_example = SHINY_PATH / "examples" / el.name / "app.py"
        if p_example.exists():
            example = SHINYLIVE_TMPL.format(p_example.read_text())
            return DOCSTRING_TMPL.format(rendered=converted, examples=example)

        return converted

    @dispatch
    def render(self, el: ds.DocstringSectionText):
        # functions like shiny.ui.tags.b have html in their docstrings, so
        # we escape them. Note that we are only escaping text sections, but
        # since these cover the top text of the docstring, it should solve
        # the immediate problem.
        result = super().render(el)
        return html.escape(result)

    def render_annotation(self, el: dc.Name | dc.Expression | None):
        return super().render_annotation(el)

    @dispatch
    def summarize(self, el: dc.Object | dc.Alias):
        result = super().summarize(el)
        return html.escape(result)
