import pytest
from quartodoc._griffe_compat import dataclasses as dc
from quartodoc._griffe_compat import docstrings as ds
from quartodoc._griffe_compat import expressions as exp

from quartodoc.renderers import MdRenderer
from quartodoc import layout, get_object, blueprint, Auto

from textwrap import indent


def indented_sections(**kwargs: str):
    return "\n\n".join([f"{k}\n" + indent(v, " " * 4) for k, v in kwargs.items()])


@pytest.fixture
def renderer():
    return MdRenderer()


# Smaller parts ----------------------------------------------------------------


def test_render_param_kwargs(renderer):
    f = get_object("quartodoc.tests.example_signature.no_annotations")
    res = renderer.render(f.parameters)

    assert ", ".join(res) == "a, b=1, *args, c, d=2, **kwargs"


def test_render_param_kwargs_annotated():
    renderer = MdRenderer(show_signature_annotations=True)
    f = get_object("quartodoc.tests.example_signature.yes_annotations")

    res = renderer.render(f.parameters)

    assert (
        ", ".join(res)
        == "a: int, b: int = 1, *args: list[str], c: int, d: int, **kwargs: dict[str, str]"
    )


@pytest.mark.parametrize(
    "src, dst",
    [
        ("example_signature.pos_only", "x, /, a, b=2"),
        ("example_signature.kw_only", "x, *, a, b=2"),
        ("example_signature.early_args", "x, *args, a, b=2, **kwargs"),
        ("example_signature.late_args", "x, a, b=2, *args, **kwargs"),
    ],
)
def test_render_param_kwonly(src, dst, renderer):
    f = get_object("quartodoc.tests", src)

    res = renderer.render(f.parameters)
    assert ", ".join(res) == dst


@pytest.mark.parametrize(
    "pair",
    [
        [ds.DocstringSectionParameters, ds.DocstringParameter],
        [ds.DocstringSectionAttributes, ds.DocstringAttribute],
        [ds.DocstringSectionReturns, ds.DocstringReturn],
    ],
)
def test_render_table_description_interlink(renderer, pair):
    interlink = "[](`abc`)"
    cls_section, cls_par = pair
    pars = cls_section([cls_par(name="x", description=interlink)])

    res = renderer.render(pars)
    assert interlink in res


@pytest.mark.parametrize(
    "section, dst",
    [
        (layout.Section(title="abc"), "## abc"),
        (layout.Section(subtitle="abc"), "### abc"),
        (layout.Section(title="abc", desc="zzz"), "## abc\n\nzzz"),
        (layout.Section(subtitle="abc", desc="zzz"), "### abc\n\nzzz"),
    ],
)
def test_render_summarize_section_title(renderer, section, dst):
    res = renderer.summarize(section)

    assert res == dst


def test_render_summarize_section_contents(renderer):
    obj = blueprint(layout.Auto(name="a_func", package="quartodoc.tests.example"))
    section = layout.Section(title="abc", desc="zzz", contents=[obj])
    res = renderer.summarize(section)

    table = (
        "| | |\n| --- | --- |\n"
        "| [a_func](#quartodoc.tests.example.a_func) | A function |"
    )
    assert res == f"## abc\n\nzzz\n\n{table}"


def test_render_doc_attribute(renderer):
    attr = ds.DocstringAttribute(
        name="abc",
        description="xyz",
        annotation=exp.ExprSubscript(exp.ExprName("Optional"), ""),
        value=1,
    )

    res = renderer.render(attr)
    print(res)

    assert res.name == "abc"
    assert res.annotation == "Optional\[\]"
    assert res.description == "xyz"


def test_render_doc_section_admonition(renderer):
    section = ds.DocstringSectionAdmonition(
        kind="see also",
        text="quartodoc.tests.example: Method for doing a thing",
        title="See Also",
    )

    res = renderer.render(section)
    print(res)

    assert res == "quartodoc.tests.example: Method for doing a thing"


def test_render_doc_section_header_anchor(renderer):
    section = ds.DocstringSection(title="a `chaotic` {.title}")

    dst = "# a `chaotic` {.title} {.doc-section .doc-section-a-chaotic-title}"

    assert renderer.render_header(section) == dst


# Big pieces -------------------------------------------------------------------
# These are mostly snapshots


@pytest.mark.parametrize("children", ["embedded", "flat", "linked"])
def test_render_doc_module(snapshot, renderer, children):
    bp = blueprint(Auto(name="quartodoc.tests.example", children=children))
    res = renderer.render(bp)

    assert res == snapshot


def test_render_annotations_complex(snapshot):
    renderer = MdRenderer(render_interlinks=True, show_signature_annotations=True)
    bp = blueprint(Auto(name="quartodoc.tests.example_signature.a_complex_signature"))
    res = renderer.render(bp)

    assert res == snapshot


def test_render_annotations_complex_no_interlinks(snapshot):
    renderer = MdRenderer(render_interlinks=False, show_signature_annotations=True)
    bp = blueprint(Auto(name="quartodoc.tests.example_signature.a_complex_signature"))
    res = renderer.render(bp)

    assert res == snapshot


@pytest.mark.parametrize("children", ["embedded", "flat"])
def test_render_doc_class(snapshot, renderer, children):
    bp = blueprint(Auto(name="quartodoc.tests.example_class.C", children=children))
    res = renderer.render(bp)

    assert res == snapshot


def test_render_doc_class_attributes_section(snapshot, renderer):
    bp = blueprint(Auto(name="quartodoc.tests.example_class.AttributesTable"))
    res = renderer.render(bp)

    assert res == snapshot


@pytest.mark.parametrize("parser", ["google", "numpy", "sphinx"])
def test_render_docstring_styles(snapshot, renderer, parser):
    package = "quartodoc.tests.example_docstring_styles"
    auto = Auto(name=f"f_{parser}", package=package)
    bp = blueprint(auto, parser=parser)

    res = renderer.render(bp)

    assert res == snapshot


def test_render_docstring_numpy_linebreaks(snapshot, renderer):
    package = "quartodoc.tests.example_docstring_styles"
    auto = Auto(name="f_numpy_with_linebreaks", package=package)
    bp = blueprint(auto)

    res = renderer.render(bp)

    assert res == snapshot


def test_render_doc_signature_name(snapshot, renderer):
    package = "quartodoc.tests"
    auto = Auto(name="example.a_func", package=package, signature_name="short")
    bp = blueprint(auto)

    res = renderer.render(bp)

    assert res == snapshot


def test_render_doc_signature_name_alias_of_alias(snapshot, renderer):
    auto = Auto(name="example.a_nested_alias", package="quartodoc.tests")
    bp = blueprint(auto)

    res = renderer.render(bp)

    assert res == snapshot


@pytest.mark.parametrize(
    "doc",
    [
        """name: int\n    A `"description"`.""",
        """int\n    A description.""",
    ],
)
def test_render_numpydoc_section_return(snapshot, doc):
    from quartodoc.parsers import get_parser_defaults
    from griffe import Parser

    full_doc = (
        f"""Parameters\n---\n{doc}\n\nReturns\n---\n{doc}\n\nAttributes\n---\n{doc}"""
    )

    el = dc.Docstring(
        value=full_doc, parser=Parser.numpy, parser_options=get_parser_defaults("numpy")
    )

    assert el.parsed is not None and len(el.parsed) == 3

    res_default = MdRenderer().render(el)
    res_list = MdRenderer(table_style="description-list").render(el)

    assert snapshot == indented_sections(
        Code=full_doc, Default=res_default, List=res_list
    )
