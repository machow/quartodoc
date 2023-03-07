import quartodoc.ast as qast

from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc
from tabulate import tabulate
from plum import dispatch
from typing import Tuple, Union

from .base import Renderer, escape, sanitize, convert_rst_link_to_md


class MdRenderer(Renderer):
    """Render docstrings to markdown.

    Parameters
    ----------
    header_level: int
        The level of the header (e.g. 1 is the biggest).
    show_signature: bool
        Whether to show the function signature.
    show_signature_annotations: bool
        Whether to show annotations in the function signature.
    display_name: str
        The default name shown for documented functions. Either "name", "relative",
        "full", or "canonical". These options range from just the function name, to its
        full path relative to its package, to including the package name, to its
        the its full path relative to its .__module__.

    Examples
    --------

    >>> from quartodoc import MdRenderer, get_object
    >>> renderer = MdRenderer(header_level=2)
    >>> f = get_object("quartodoc", "get_object")
    >>> print(renderer.render(f)[:81])
    ## get_object
    `get_object(module: str, object_name: str, parser: str = 'numpy')`

    """

    style = "markdown"

    def __init__(
        self,
        header_level: int = 2,
        show_signature: bool = True,
        show_signature_annotations: bool = False,
        display_name: str = "name",
        hook_pre=None,
    ):
        self.header_level = header_level
        self.show_signature = show_signature
        self.show_signature_annotations = show_signature_annotations
        self.display_name = display_name
        self.hook_pre = hook_pre

    def _render_annotation(self, el: "str | dc.Name | dc.Expression | None"):
        if isinstance(el, (type(None), str)):
            return el

        # TODO: maybe there is a way to get tabulate to handle this?
        # unescaped pipes screw up table formatting
        return sanitize(el.full)

    def _fetch_object_dispname(self, el: "dc.Alias | dc.Object"):
        # TODO: copied from Builder, should move into util function
        if self.display_name == "name":
            return el.name
        elif self.display_name == "relative":
            return ".".join(el.path.split(".")[1:])

        elif self.display_name == "full":
            return el.path

        elif self.display_name == "canonical":
            return el.canonical_path

        raise ValueError(f"Unsupported display_name: `{self.display_name}`")

    # signature method --------------------------------------------------------

    @dispatch
    def signature(self, el: dc.Alias):
        return self.signature(el.target)

    @dispatch
    def signature(self, el: Union[dc.Class, dc.Function]):
        name = self._fetch_object_dispname(el)
        pars = self.render(el.parameters)

        return f"`{name}({pars})`"

    @dispatch
    def signature(self, el: Union[dc.Module, dc.Attribute]):
        name = self._fetch_object_dispname(el)
        return f"`{name}`"

        
    # render method -----------------------------------------------------------

    @dispatch
    def render(self, el):
        raise NotImplementedError(f"Unsupported type: {type(el)}")

    @dispatch
    def render(self, el: str):
        return el

    @dispatch
    def render(self, el: Union[dc.Object, dc.Alias]):
        """Render high level objects representing functions, classes, etc.."""

        str_sig = self.signature(el)

        _str_dispname = self._fetch_object_dispname(el)
        _anchor = f"{{ #{_str_dispname} }}"
        str_title = f"{'#' * self.header_level} {_str_dispname} {_anchor}"

        str_body = []
        if el.docstring is None:
            pass
        else:
            for section in el.docstring.parsed:
                new_el = qast.transform(section)
                title = new_el.kind.value
                body = self.render(new_el)

                if title != "text":
                    header = f"{'#' * (self.header_level + 1)} {title.title()}"
                    str_body.append("\n\n".join([header, body]))
                else:
                    str_body.append(body)

        if self.show_signature:
            parts = [str_title, str_sig, *str_body]
        else:
            parts = [str_title, *str_body]

        return "\n\n".join(parts)

    # signature parts -------------------------------------------------------------

    @dispatch
    def render(self, el: dc.Parameters):
        return ", ".join(map(self.render, el))

    @dispatch
    def render(self, el: dc.Parameter):
        # TODO: missing annotation
        splats = {dc.ParameterKind.var_keyword, dc.ParameterKind.var_positional}
        has_default = el.default and el.kind not in splats

        annotation = self._render_annotation(el.annotation)
        if self.show_signature_annotations:
            if annotation and has_default:
                return f"{el.name}: {el.annotation} = {el.default}"
            elif annotation:
                return f"{el.name}: {el.annotation}"
        elif has_default:
            return f"{el.name}={el.default}"

        return el.name

    # docstring parts -------------------------------------------------------------

    # text ----
    # note this can be a number of things. for example, opening docstring text,
    # or a section with a header not included in the numpydoc standard
    @dispatch
    def render(self, el: ds.DocstringSectionText):
        new_el = qast.transform(el)
        if isinstance(new_el, ds.DocstringSectionText):
            # ensures we don't recurse forever
            return el.value

        return self.render(new_el)

    # parameters ----

    @dispatch
    def render(self, el: ds.DocstringSectionParameters):
        rows = list(map(self.render, el.value))
        header = ["Name", "Type", "Description", "Default"]

        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def render(self, el: ds.DocstringParameter) -> Tuple[str]:
        # TODO: if default is not, should return the word "required" (unescaped)
        default = "required" if el.default is None else escape(el.default)

        annotation = self._render_annotation(el.annotation)
        return (escape(el.name), annotation, sanitize(el.description), default)

    # attributes ----

    @dispatch
    def render(self, el: ds.DocstringSectionAttributes):
        header = ["Name", "Type", "Description"]
        rows = list(map(self.render, el.value))

        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def render(self, el: ds.DocstringAttribute):
        annotation = self._render_annotation(el.annotation)
        return el.name, self.render(annotation), el.description

    # warnings ----

    @dispatch
    def render(self, el: qast.DocstringSectionWarnings):
        return el.value

    # see also ----

    @dispatch
    def render(self, el: qast.DocstringSectionSeeAlso):
        # TODO: attempt to parse See Also sections
        return convert_rst_link_to_md(el.value)

    # notes ----

    @dispatch
    def render(self, el: qast.DocstringSectionNotes):
        return el.value

    # examples ----

    @dispatch
    def render(self, el: ds.DocstringSectionExamples):
        # its value is a tuple: DocstringSectionKind["text" | "examples"], str
        data = map(qast.transform, el.value)
        return "\n\n".join(list(map(self.render, data)))

    @dispatch
    def render(self, el: qast.ExampleCode):
        return f"""```python
{el.value}
```"""

    @dispatch
    def render(self, el: qast.ExampleText):
        return el.value

    # returns ----

    @dispatch
    def render(self, el: Union[ds.DocstringSectionReturns, ds.DocstringSectionRaises]):
        rows = list(map(self.render, el.value))
        header = ["Type", "Description"]

        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def render(self, el: Union[ds.DocstringReturn, ds.DocstringRaise]):
        # similar to DocstringParameter, but no name or default
        annotation = self._render_annotation(el.annotation)
        return (annotation, el.description)

    # unsupported parts ----

    @dispatch.multi(
        (ds.DocstringAdmonition,),
        (ds.DocstringDeprecated,),
        (ds.DocstringWarn,),
        (ds.DocstringYield,),
        (ds.DocstringReceive,),
        (ds.DocstringAttribute,),
    )
    def render(self, el):
        raise NotImplementedError(f"{type(el)}")
