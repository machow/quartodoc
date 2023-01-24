from importlib.resources import files
from quartodoc import MdRenderer
from plum import dispatch

from griffe import dataclasses as dc


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
    def to_md(self, el: dc.Object):
        rendered = super().to_md(el)

        p_example = SHINY_PATH / "examples" / el.name / "app.py"
        if p_example.exists():
            example = SHINYLIVE_TMPL.format(p_example.read_text())
            return DOCSTRING_TMPL.format(rendered=rendered, examples=example)

        return rendered
