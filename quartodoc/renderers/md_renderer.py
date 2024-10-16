from __future__ import annotations

import black
import re
import quartodoc.ast as qast

from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from .._griffe_compat import docstrings as ds
from .._griffe_compat import dataclasses as dc
from .._griffe_compat import expressions as expr
from tabulate import tabulate
from plum import dispatch
from typing import Any, Literal, Tuple, Union, Optional
from quartodoc import layout
from quartodoc.pandoc.blocks import DefinitionList
from quartodoc.pandoc.inlines import Span, Strong, Attr, Code, Inlines

from .base import Renderer, escape, sanitize, convert_rst_link_to_md


def _has_attr_section(el: dc.Docstring | None):
    if el is None:
        return False

    return any([isinstance(x, ds.DocstringSectionAttributes) for x in el.parsed])


def _sanitize_title(title: str):
    """Replace characters so that title can be used as an anchor, by

    Approach:
       * replace spaces with -, then
       * stripping non alphanumeric characters

    Examples
    --------

    >>> _sanitize_title("a b c")
    'a-b-c'
    >>> _sanitize_title("a b! c")
    'a-b-c'
    >>> _sanitize_title("a`b`c{")
    'abc'

    """

    return re.sub(r"[^a-zA-Z0-9-]+", "", title.replace(" ", "-"))


@dataclass
class ParamRow:
    name: str | None
    description: str
    annotation: str | None = None
    default: str | None = None

    def to_definition_list(self):
        name = self.name
        anno = self.annotation
        desc = sanitize(self.description, allow_markdown=True)
        default = sanitize(str(self.default), escape_quotes=True)

        part_name = (
            Span(Strong(name), Attr(classes=["parameter-name"]))
            if name is not None
            else ""
        )
        part_anno = (
            Span(anno, Attr(classes=["parameter-annotation"]))
            if anno is not None
            else ""
        )

        # TODO: _required_ is set when parsing parameters, but only used
        # in the table display format, not description lists....
        # by this stage _required_ is basically a special token to indicate
        # a required argument.
        if self.default is not None:
            part_default_sep = Span(" = ", Attr(classes=["parameter-default-sep"]))
            part_default = Span(default, Attr(classes=["parameter-default"]))
        else:
            part_default_sep = ""
            part_default = ""

        part_desc = desc if desc is not None else ""

        anno_sep = Span(":", Attr(classes=["parameter-annotation-sep"]))

        # TODO: should code wrap the whole thing like this?
        param = Code(
            str(
                Inlines(
                    [part_name, anno_sep, part_anno, part_default_sep, part_default]
                )
            )
        ).html
        return (param, part_desc)

    def to_tuple(self, style: Literal["parameters", "attributes", "returns"]):
        name = self.name
        description = sanitize(self.description, allow_markdown=True)

        if style == "parameters":
            default = "_required_" if self.default is None else escape(self.default)
            return (name, self.annotation, description, default)
        elif style == "attributes":
            return (name, self.annotation, description)
        elif style == "returns":
            return (name, self.annotation, description)

        raise NotImplementedError(f"Unsupported table style: {style}")


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
        render_interlinks=False,
        # table_style="description-list",
        table_style="table",
    ):
        self.header_level = header_level
        self.show_signature = show_signature
        self.show_signature_annotations = show_signature_annotations
        self.display_name = display_name
        self.hook_pre = hook_pre
        self.render_interlinks = render_interlinks
        self.table_style = table_style

        self.crnt_header_level = self.header_level

    @contextmanager
    def _increment_header(self, n=1):
        self.crnt_header_level += n
        try:
            yield
        finally:
            self.crnt_header_level -= n

    def _fetch_object_dispname(self, el: "dc.Alias | dc.Object"):
        # TODO: copied from Builder, should move into util function
        if self.display_name in {"name", "short"}:
            return el.name
        elif self.display_name == "relative":
            return ".".join(el.path.split(".")[1:])

        elif self.display_name == "full":
            return el.path

        elif self.display_name == "canonical":
            return el.canonical_path

        raise ValueError(f"Unsupported display_name: `{self.display_name}`")

    def _fetch_method_parameters(self, el: dc.Function):
        # adapted from mkdocstrings-python jinja tempalate
        if el.parent and el.parent.is_class and len(el.parameters) > 0:
            if el.parameters[0].name in {"self", "cls"}:
                return dc.Parameters(*list(el.parameters)[1:])

        return el.parameters

    def _render_table(
        self,
        rows,
        headers,
        style: Literal["parameters", "attributes", "returns"],
    ):
        if self.table_style == "description-list":
            return str(DefinitionList([row.to_definition_list() for row in rows]))
        else:
            row_tuples = [row.to_tuple(style) for row in rows]
            table = tabulate(row_tuples, headers=headers, tablefmt="github")
            return table

    # render_annotation method --------------------------------------------------------

    @dispatch
    def render_annotation(self, el: str) -> str:
        """Special hook for rendering a type annotation.
        Parameters
        ----------
        el:
            An object representing a type annotation.
        """
        return sanitize(el, escape_quotes=True)

    @dispatch
    def render_annotation(self, el: None) -> str:
        return ""

    @dispatch
    def render_annotation(self, el: expr.ExprName) -> str:
        # TODO: maybe there is a way to get tabulate to handle this?
        # unescaped pipes screw up table formatting
        if self.render_interlinks:
            return f"[{sanitize(el.name)}](`{el.canonical_path}`)"

        return sanitize(el.name)

    @dispatch
    def render_annotation(self, el: expr.Expr) -> str:
        return "".join(map(self.render_annotation, el))

    # signature method --------------------------------------------------------

    @dispatch
    def signature(self, el: layout.Doc):
        """Return a string representation of an object's signature."""
        orig = self.display_name

        # set signature path, generate signature, then set back
        # TODO: this is for backwards compatibility with the old approach
        # of only defining signature over griffe objects, which projects
        # like shiny currently extend
        self.display_name = el.signature_name
        res = self.signature(el.obj)
        self.display_name = orig

        return res

    @dispatch
    def signature(self, el: dc.Alias, source: Optional[dc.Alias] = None):
        return self.signature(el.final_target, el)

    @dispatch
    def signature(
        self, el: Union[dc.Class, dc.Function], source: Optional[dc.Alias] = None
    ):
        name = self._fetch_object_dispname(source or el)
        pars = self.render(self._fetch_method_parameters(el))

        flat_sig = f"{name}({', '.join(pars)})"
        if len(flat_sig) > 80:
            indented = [" " * 4 + par for par in pars]
            sig = "\n".join([f"{name}(", *indented, ")"])
        else:
            sig = flat_sig

        return f"```python\n{sig}\n```"

    @dispatch
    def signature(
        self, el: Union[dc.Module, dc.Attribute], source: Optional[dc.Alias] = None
    ):
        name = self._fetch_object_dispname(source or el)
        return f"`{name}`"

    @dispatch
    def render_header(self, el: layout.Doc) -> str:
        """Render the header of a docstring, including any anchors."""
        _str_dispname = el.name

        # TODO: support anchors that are not fully qualified paths?
        # e.g. get_object, rather than quartodoc.get_object
        _anchor = f"{{ #{el.obj.path} }}"
        return f"{'#' * self.crnt_header_level} {_str_dispname} {_anchor}"

    @dispatch
    def render_header(self, el: ds.DocstringSection) -> str:
        title = el.title or el.kind.value.title()
        anchor_part = _sanitize_title(title.lower())
        _classes = [".doc-section", f".doc-section-{anchor_part}"]
        _str_classes = " ".join(_classes)
        return f"{'#' * self.crnt_header_level} {title} {{{_str_classes}}}"

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
    def render(self, el: layout.Interlaced):
        # render a sequence of objects with like-sections together.
        # restrict its behavior to documenting functions for now ----
        for doc in el.contents:
            if not isinstance(doc, (layout.DocFunction, layout.DocAttribute)):
                raise NotImplementedError(
                    "Can only render Interlaced elements if all content elements"
                    " are function or attribute docs."
                    f" Found an element of type {type(doc)}, with name {doc.name}"
                )

        # render ----
        # currently, we use everything from the first function, and just render
        # the signatures together
        first_doc = el.contents[0]
        objs = [doc.obj for doc in el.contents]

        if first_doc.obj.docstring is None:
            raise ValueError("The first element of Interlaced must have a docstring.")

        str_title = self.render_header(first_doc)
        str_sig = "\n\n".join(map(self.signature, objs))
        str_body = []

        # TODO: we should also interlace parameters and examples
        # parsed = map(qast.transform, [x.docstring.parsed for x in objs if x.docstring])

        # TODO: this is copied from the render method for dc.Object
        for section in qast.transform(first_doc.obj.docstring.parsed):
            title = section.title or section.kind.value
            body = self.render(section)

            if title != "text":
                header = f"{'#' * (self.crnt_header_level + 1)} {title.title()}"
                str_body.append("\n\n".join([header, body]))
            else:
                str_body.append(body)

        if self.show_signature:
            parts = [str_title, str_sig, *str_body]
        else:
            parts = [str_title, *str_body]

        return "\n\n".join(parts)

    @dispatch
    def render(self, el: layout.Doc):
        raise NotImplementedError(f"Unsupported Doc type: {type(el)}")

    @dispatch
    def render(self, el: Union[layout.DocClass, layout.DocModule]):
        title = self.render_header(el)

        attr_docs = []
        meth_docs = []
        class_docs = []

        if el.members:
            sub_header = "#" * (self.crnt_header_level + 1)
            raw_attrs = [x for x in el.members if x.obj.is_attribute]
            raw_meths = [x for x in el.members if x.obj.is_function]
            raw_classes = [x for x in el.members if x.obj.is_class]

            header = "| Name | Description |\n| --- | --- |"

            # attribute summary table ----
            # docstrings can define an attributes section. If that exists on
            # then we skip summarizing each attribute into a table.
            # TODO: for now, we skip making an attribute table on classes, unless
            # they contain an attributes section in the docstring
            if (
                raw_attrs
                and not _has_attr_section(el.obj.docstring)
                # TODO: what should backwards compat be?
                # and not isinstance(el, layout.DocClass)
            ):

                _attrs_table = "\n".join(map(self.summarize, raw_attrs))
                attrs = f"{sub_header} Attributes\n\n{header}\n{_attrs_table}"
                attr_docs.append(attrs)

            # classes summary table ----
            if raw_classes:
                _summary_table = "\n".join(map(self.summarize, raw_classes))
                section_name = "Classes"
                objs = f"{sub_header} {section_name}\n\n{header}\n{_summary_table}"
                class_docs.append(objs)

                n_incr = 1 if el.flat else 2
                with self._increment_header(n_incr):
                    class_docs.extend(
                        [
                            self.render(x)
                            for x in raw_classes
                            if isinstance(x, layout.Doc)
                        ]
                    )

            # method summary table ----
            if raw_meths:
                _summary_table = "\n".join(map(self.summarize, raw_meths))
                section_name = (
                    "Methods" if isinstance(el, layout.DocClass) else "Functions"
                )
                objs = f"{sub_header} {section_name}\n\n{header}\n{_summary_table}"
                meth_docs.append(objs)

                # TODO use context manager, or context variable?
                n_incr = 1 if el.flat else 2
                with self._increment_header(n_incr):
                    meth_docs.extend(
                        [self.render(x) for x in raw_meths if isinstance(x, layout.Doc)]
                    )

        str_sig = self.signature(el)
        sig_part = [str_sig] if self.show_signature else []

        with self._increment_header():
            body = self.render(el.obj)

        return "\n\n".join(
            [title, *sig_part, body, *attr_docs, *class_docs, *meth_docs]
        )

    @dispatch
    def render(self, el: Union[layout.DocFunction, layout.DocAttribute]):
        title = self.render_header(el)

        str_sig = self.signature(el)
        sig_part = [str_sig] if self.show_signature else []

        with self._increment_header():
            body = self.render(el.obj)

        return "\n\n".join([title, *sig_part, body])

    # render griffe objects ===================================================

    @dispatch
    def render(self, el: Union[dc.Object, dc.Alias]):
        """Render high level objects representing functions, classes, etc.."""

        if el.docstring is None:
            return ""
        else:
            return self.render(el.docstring)

    @dispatch
    def render(self, el: dc.Docstring):
        str_body = []
        patched_sections = qast.transform(el.parsed)

        for section in patched_sections:
            title = section.title or section.kind.value
            body: str = self.render(section)

            if title != "text":
                header = self.render_header(section)
                # header = f"{'#' * (self.crnt_header_level + 1)} {title.title()}"
                str_body.append("\n\n".join([header, body]))
            else:
                str_body.append(body)

        parts = [*str_body]

        return "\n\n".join(parts)

    # signature parts -------------------------------------------------------------

    @dispatch
    def render(self, el: dc.Parameters) -> "list":
        # index for switch from positional to kw args (via an unnamed *)
        try:
            kw_only = [par.kind for par in el].index(dc.ParameterKind.keyword_only)
        except ValueError:
            kw_only = None

        # index for final positionly only args (via /)
        try:
            pos_only = max(
                [
                    ii
                    for ii, el in enumerate(el)
                    if el.kind == dc.ParameterKind.positional_only
                ]
            )
        except ValueError:
            pos_only = None

        pars = list(map(self.render, el))

        # insert a single `*,` argument to represent the shift to kw only arguments,
        # only if the shift to kw_only was not triggered by *args (var_positional)
        if (
            kw_only is not None
            and kw_only > 0
            and el[kw_only - 1].kind != dc.ParameterKind.var_positional
        ):
            pars.insert(kw_only, "*")

        # insert a single `/, ` argument to represent shift from positional only arguments
        # note that this must come before a single *, so it's okay that both this
        # and block above insert into pars
        if pos_only is not None:
            pars.insert(pos_only + 1, "/")

        return pars

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

        annotation = el.annotation  # self.render_annotation(el.annotation)
        name = el.name

        if self.show_signature_annotations:
            if annotation and has_default:
                res = f"{glob}{name}: {annotation} = {el.default}"
            elif annotation:
                res = f"{glob}{name}: {annotation}"
            else:
                res = f"{glob}{name}"

        elif has_default:
            res = f"{glob}{name}={el.default}"
        else:
            res = f"{glob}{name}"

        return res

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
        rows: "list[ParamRow]" = list(map(self.render, el.value))
        header = ["Name", "Type", "Description", "Default"]
        return self._render_table(rows, header, "parameters")

    @dispatch
    def render(self, el: ds.DocstringParameter) -> ParamRow:
        annotation = self.render_annotation(el.annotation)
        return ParamRow(
            el.name, el.description, annotation=annotation, default=el.default
        )

    # attributes ----

    @dispatch
    def render(self, el: ds.DocstringSectionAttributes):
        header = ["Name", "Type", "Description"]
        rows = list(map(self.render, el.value))

        return self._render_table(rows, header, "attributes")

    @dispatch
    def render(self, el: ds.DocstringAttribute) -> ParamRow:
        return ParamRow(
            el.name,
            el.description or "",
            annotation=self.render_annotation(el.annotation),
        )

    # admonition ----
    # note this can be a see-also, warnings, or notes section
    # from the googledoc standard
    @dispatch
    def render(self, el: ds.DocstringSectionAdmonition):
        kind = el.title.lower()
        if kind in ["notes", "warnings"]:
            return el.value.description
        elif kind == "see also":
            # TODO: attempt to parse See Also sections
            return convert_rst_link_to_md(el.value.description)

        return el.value.description

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
        header = ["Name", "Type", "Description"]

        return self._render_table(rows, header, "returns")

    @dispatch
    def render(self, el: ds.DocstringReturn):
        # similar to DocstringParameter, but no name or default
        return ParamRow(
            el.name,
            el.description,
            annotation=self.render_annotation(el.annotation),
        )

    @dispatch
    def render(self, el: ds.DocstringRaise) -> ParamRow:
        # similar to DocstringParameter, but no name or default
        return ParamRow(
            None,
            el.description,
            annotation=self.render_annotation(el.annotation),
        )

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
        return f"| {link} | {sanitize(description, allow_markdown=True)} |"

    @dispatch
    def summarize(self, el):
        """Produce a summary table."""

        raise NotImplementedError(f"Unsupported type: {type(el)}")

    @dispatch
    def summarize(self, el: layout.Layout):
        rendered_sections = list(map(self.summarize, el.sections))
        return "\n\n".join(rendered_sections)

    @dispatch
    def summarize(self, el: layout.Section):
        desc = f"\n\n{el.desc}" if el.desc is not None else ""
        if el.title is not None:
            header = f"## {el.title}{desc}"
        elif el.subtitle is not None:
            header = f"### {el.subtitle}{desc}"
        else:
            header = ""

        if el.contents:
            thead = "| | |\n| --- | --- |"

            rendered = []
            for child in el.contents:
                rendered.append(self.summarize(child))

            str_func_table = "\n".join([thead, *rendered])
            return f"{header}\n\n{str_func_table}"

        return header

    @dispatch
    def summarize(self, el: layout.Page):
        if el.summary is not None:
            # TODO: assumes that files end with .qmd
            return self._summary_row(
                f"[{el.summary.name}]({el.path}.qmd)", el.summary.desc
            )

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
        return self.summarize(el.contents[0], el.path, shorten=True)

    @dispatch
    def summarize(self, el: layout.Interlaced, *args, **kwargs):
        rows = [self.summarize(doc, *args, **kwargs) for doc in el.contents]

        return "\n".join(rows)

    @dispatch
    def summarize(
        self, el: layout.Doc, path: Optional[str] = None, shorten: bool = False
    ):
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
        return self._summary_row(f"[](`~{el.name}`)", description)

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
