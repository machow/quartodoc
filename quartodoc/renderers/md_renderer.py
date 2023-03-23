from __future__ import annotations

import quartodoc.ast as qast

from contextlib import contextmanager
from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc
from tabulate import tabulate
from plum import dispatch
from typing import Tuple, Union, Optional
from quartodoc import layout

from .base import Renderer, escape, sanitize, convert_rst_link_to_md


def _has_attr_section(el: dc.Docstring | None):
    if el is None:
        return False

    return any([isinstance(x, ds.DocstringSectionAttributes) for x in el.parsed])



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
        header_level: int = 1,
        show_signature: bool = True,
        show_signature_annotations: bool = False,
        display_name: str = "relative",
        hook_pre=None,
        use_interlinks = False,

    ):
        self.header_level = header_level
        self.show_signature = show_signature
        self.show_signature_annotations = show_signature_annotations
        self.display_name = display_name
        self.hook_pre = hook_pre
        self.use_interlinks = use_interlinks

        self.crnt_header_level = self.header_level

    @contextmanager
    def _increment_header(self, n = 1):
        self.crnt_header_level += n
        try:
            yield
        finally: 
            self.crnt_header_level -= n


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

    def render_annotation(self, el: "str | dc.Name | dc.Expression | None"):
        """Special hook for rendering a type annotation.

        Parameters
        ----------
        el:
            An object representing a type annotation.
            
        """

        if isinstance(el, (type(None), str)):
            return el

        # TODO: maybe there is a way to get tabulate to handle this?
        # unescaped pipes screw up table formatting
        if isinstance(el, dc.Name):
            return sanitize(el.source)

        return sanitize(el.full)

    # signature method --------------------------------------------------------

    @dispatch
    def signature(self, el: dc.Alias, source: Optional[dc.Alias] = None):
        """Return a string representation of an object's signature."""

        return self.signature(el.target, el)

    @dispatch
    def signature(self, el: Union[dc.Class, dc.Function], source: Optional[dc.Alias] = None):
        name = self._fetch_object_dispname(source or el)
        pars = self.render(el.parameters)

        return f"`{name}({pars})`"

    @dispatch
    def signature(self, el: Union[dc.Module, dc.Attribute], source: Optional[dc.Alias] = None):
        name = self._fetch_object_dispname(source or el)
        return f"`{name}`"


    @dispatch
    def render_header(self, el: layout.Doc):
        """Render the header of a docstring, including any anchors."""
        _str_dispname = el.name

        # TODO: support anchors that are not fully qualified paths?
        # e.g. get_object, rather than quartodoc.get_object
        _anchor = f"{{ #{el.obj.path} }}"
        return f"{'#' * self.crnt_header_level} {_str_dispname} {_anchor}"

        
    # render method -----------------------------------------------------------

    @dispatch
    def render(self, el):
        """Return a string representation of an object, or layout element."""

        raise NotImplementedError(f"Unsupported type: {type(el)}")

    @dispatch
    def render(self, el: str):
        return el

    # render layouts ==========================================================

    @dispatch
    def render(self, el: layout.Page):
        if el.summary:
            sum_ = el.summary
            header = [f"{'#' * self.crnt_header_level} {sum_.name}\n\n{sum_.desc}"]
        else:
            header = []

        result = map(self.render, el.contents)

        return "\n\n".join([*header, *result])

    @dispatch
    def render(self, el: layout.Section):
        section_top = f"{'#' * self.crnt_header_level} {el.title}\n\n{el.desc}"

        with self._increment_header():
            body = list(map(self.render, el.contents))

        return "\n\n".join([section_top, *body])

    @dispatch
    def render(self, el: layout.Doc):
        raise NotImplementedError(f"Unsupported Doc type: {type(el)}")

    @dispatch
    def render(self, el: Union[layout.DocClass, layout.DocModule]):
        title = self.render_header(el)

        extra_parts = []
        meth_docs = []
        if el.members:
            sub_header = "#" * (self.crnt_header_level + 1)
            raw_attrs = [x for x in el.members if x.obj.is_attribute]
            raw_meths = [x for x in el.members if x.obj.is_function]


            header = "| Name | Description |\n| --- | --- |"

            # attribute summary table ----
            # docstrings can define an attributes section. If that exists on
            # then we skip summarizing each attribute into a table.
            # TODO: for now, we skip making an attribute table on classes, unless
            # they contain an attributes section in the docstring
            if (
                    raw_attrs
                    and not _has_attr_section(el.obj.docstring)
                    and not isinstance(el, layout.DocClass)
                ):

                _attrs_table = "\n".join(map(self.summarize, raw_attrs))
                attrs = f"{sub_header} Attributes\n\n{header}\n{_attrs_table}"
                extra_parts.append(attrs)

            # method summary table ----
            if raw_meths:
                _meths_table = "\n".join(map(self.summarize, raw_meths))
                section_name = (
                    "Methods" if isinstance(el, layout.DocClass)
                    else "Functions"
                )
                meths = f"{sub_header} {section_name}\n\n{header}\n{_meths_table}"
                extra_parts.append(meths)

                # TODO use context manager, or context variable?
                with self._increment_header(2):
                    meth_docs = [self.render(x) for x in raw_meths if isinstance(x, layout.Doc)]

        body = self.render(el.obj)
        return "\n\n".join([title, body, *extra_parts, *meth_docs])

    @dispatch
    def render(self, el: layout.DocFunction):
        title = self.render_header(el)

        return "\n\n".join([title, self.render(el.obj)])

    @dispatch
    def render(self, el: layout.DocAttribute):
        title = self.render_header(el)
        return "\n\n".join([title, self.render(el.obj)])

    # render griffe objects ===================================================

    @dispatch
    def render(self, el: Union[dc.Object, dc.Alias]):
        """Render high level objects representing functions, classes, etc.."""

        str_sig = self.signature(el)

        str_body = []
        if el.docstring is None:
            pass
        else:
            patched_sections = qast.transform(el.docstring.parsed)
            for section in patched_sections:
                title = section.title or section.kind.value
                body = self.render(section)

                if title != "text":
                    header = f"{'#' * (self.crnt_header_level + 1)} {title.title()}"
                    str_body.append("\n\n".join([header, body]))
                else:
                    str_body.append(body)

        if self.show_signature:
            parts = [str_sig, *str_body]
        else:
            parts = [*str_body]

        return "\n\n".join(parts)

    # signature parts -------------------------------------------------------------

    @dispatch
    def render(self, el: dc.Parameters):
        try:
            kw_only = [par.kind for par in el].index(dc.ParameterKind.keyword_only)
        except ValueError:
            kw_only = None
        
        pars = list(map(self.render, el))

        if kw_only is not None:
            pars.insert(kw_only, sanitize("*"))

        return ", ".join(pars)

    @dispatch
    def render(self, el: dc.Parameter):
        # TODO: missing annotation
        splats = {dc.ParameterKind.var_keyword, dc.ParameterKind.var_positional}
        has_default = el.default and el.kind not in splats

        if el.kind == dc.ParameterKind.var_keyword:
            glob = "**"
        elif el.kind == dc.ParameterKind.var_positional:
            glob = "*"
        else:
            glob = ""

        annotation = self.render_annotation(el.annotation)
        if self.show_signature_annotations:
            if annotation and has_default:
                res = f"{glob}{el.name}: {el.annotation} = {el.default}"
            elif annotation:
                res = f"{glob}{el.name}: {el.annotation}"
        elif has_default:
            res = f"{glob}{el.name}={el.default}"
        else:
            res = el.name

        return sanitize(res)

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

        annotation = self.render_annotation(el.annotation)
        return (escape(el.name), annotation, sanitize(el.description), default)

    # attributes ----

    @dispatch
    def render(self, el: ds.DocstringSectionAttributes):
        header = ["Name", "Type", "Description"]
        rows = list(map(self.render, el.value))

        return tabulate(rows, header, tablefmt="github")

    @dispatch
    def render(self, el: ds.DocstringAttribute):
        annotation = self.render_annotation(el.annotation)
        return el.name, self.render_annotation(annotation), el.description

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
        annotation = self.render_annotation(el.annotation)
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

    
    # Summarize ===============================================================
    # this method returns a summary description, such as a table summarizing a
    # layout.Section, or a row in the table for layout.Page or layout.DocFunction.

    @staticmethod
    def _summary_row(link, description):
        return f"| {link} | {sanitize(description)} |"

    @dispatch
    def summarize(self, el):
        """Produce a summary table."""

        raise NotImplementedError("Unsupported type: {type(el)}")

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
        if el.summary is not None:
            return self._summary_row(f"[{el.summary.name}]({el.path})", el.summary.desc)

        if len(el.contents) > 1 and not el.flatten:
            raise ValueError(
                "Cannot summarize Page. Either set its `summary` attribute with name "
                "and description details, or set `flatten` to True."
            )

        else:
            rows = [self.summarize(entry, el.path) for entry in el.contents]
            return "\n".join(rows)

    @dispatch
    def summarize(self, el: layout.MemberPage):
        # TODO: model should validate these only have a single entry
        return self.summarize(el.contents[0], el.path, shorten = True)

    @dispatch
    def summarize(self, el: layout.Doc, path: Optional[str] = None, shorten: bool = False):
        if path is None:
            link = f"[{el.name}](#{el.anchor})"
        else:
            # TODO: assumes that files end with .qmd
            link = f"[{el.name}]({path}.qmd#{el.anchor})"

        description = self.summarize(el.obj)
        return self._summary_row(link, description)

    @dispatch
    def summarize(self, el: layout.Link):
         description = self.summarize(el.obj)
         return self._summary_row(f"[](`{el.name}`)", description)

    @dispatch
    def summarize(self, obj: Union[dc.Object, dc.Alias]) -> str:
        """Test"""
        # get high-level description
        doc = obj.docstring
        if doc is None:
            docstring_parts = []
        else:
            docstring_parts = doc.parsed

        if len(docstring_parts) and isinstance(
            docstring_parts[0], ds.DocstringSectionText
        ):
            description = docstring_parts[0].value
            short = description.split("\n")[0]

            return short

        return ""
