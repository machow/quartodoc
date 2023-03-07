from quartodoc import get_function, MdRenderer
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


def test_replace_docstring():
    from quartodoc.autosummary import get_object, replace_docstring
    from quartodoc.tests.example_dynamic import f

    obj = get_object("quartodoc", "tests.example_dynamic.f")
    old = obj.docstring

    replace_docstring(obj, f)
    assert obj.docstring is not old

    # just check the end of the piece dynamically added to docstring, since
    # griffe strips the left padding from docstrings.
    assert obj.docstring.value.endswith("I am a note")
