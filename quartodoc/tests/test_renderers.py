import pytest
import griffe.docstrings.dataclasses as ds
import griffe.expressions as exp

from quartodoc.renderers import MdRenderer
from quartodoc import layout, get_object, blueprint, Auto


@pytest.fixture
def renderer():
    return MdRenderer()


def test_render_param_kwargs(renderer):
    f = get_object("quartodoc.tests.example_signature.no_annotations")
    res = renderer.render(f.parameters)

    assert res == "a, b=1, *args, c, d=2, **kwargs"


def test_render_param_kwargs_annotated():
    renderer = MdRenderer(show_signature_annotations=True)
    f = get_object("quartodoc.tests.example_signature.yes_annotations")

    res = renderer.render(f.parameters)

    assert (
        res
        == "a: int, b: int = 1, *args: list\\[str\\], c: int, d: int, **kwargs: dict\\[str, str\\]"
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
    assert res == dst


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
        annotation=exp.Expression(exp.Name("Optional", full="Optional"), "[", "]"),
        value=1,
    )

    res = renderer.render(attr)

    assert res == ["abc", r"Optional\[\]", "xyz"]


@pytest.mark.parametrize("children", ["embedded", "flat"])
def test_render_doc_module(snapshot, renderer, children):
    bp = blueprint(Auto(name="quartodoc.tests.example", children=children))
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


def test_render_doc_signature_path(snapshot, renderer):
    package = "quartodoc.tests"
    auto = Auto(name="example.a_func", package=package, signature_path="short")
    bp = blueprint(auto)

    res = renderer.render(bp)

    assert res == snapshot


def test_render_source(renderer):
    obj = get_object("quartodoc.tests.example.a_func")
    res = renderer.render_source(obj)

    code = '''\
def a_func():
    """A function"""\
'''

    res == f"<code><pre>{code}</pre></code>"


def test_render_doc_show_source(renderer, snapshot):
    package = "quartodoc.tests.example_docstring_styles"
    auto = Auto(name="f_quarto_block_in_docstring", package=package, show_source=True)
    bp = blueprint(auto)

    res = renderer.render(bp)

    assert res == snapshot
