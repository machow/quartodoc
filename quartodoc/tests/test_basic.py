from quartodoc import get_object, get_function, MdRenderer
from griffe.docstrings import dataclasses as ds


def test_get_function():
    f_obj = get_function("quartodoc", "get_function")

    assert f_obj.name == "get_function"
    assert any(
        isinstance(x, ds.DocstringSectionExamples) for x in f_obj.docstring.parsed
    )


def test_renderer_render():
    # TODO: use snapshots?
    f_obj = get_function("quartodoc", "get_function")

    renderer = MdRenderer()
    assert isinstance(renderer.render(f_obj), str)


def test_attribute_docstring():
    a = get_object("quartodoc", "tests.example_attribute.a")
    assert a.docstring.value == "I am an attribute docstring"


def test_class_attribute_docstring():
    a = get_object("quartodoc", "tests.example_attribute.SomeClass.a")
    assert a.docstring.value == "I am a class attribute docstring"


def test_render_attribute():
    # TODO: snapshot tests
    a = get_object("quartodoc", "tests.example_attribute.a")

    assert (
        MdRenderer().render(a)
        == """\
## a { #a }

`a`

I am an attribute docstring"""
    )
