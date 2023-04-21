import pytest

from quartodoc.renderers import MdRenderer
from quartodoc import get_object

# TODO: tests in test_basic.py also use the renderer, so we should move them here.


@pytest.fixture
def renderer():
    return MdRenderer()


def test_render_param_kwargs(renderer):
    f = get_object("quartodoc.tests.example_signature.no_annotations")
    res = renderer.render(f.parameters)

    assert res == "a, b=1, *args, *, c, d=2, **kwargs"


def test_render_param_kwargs_annotated():
    renderer = MdRenderer(show_signature_annotations=True)
    f = get_object("quartodoc.tests.example_signature.yes_annotations")

    res = renderer.render(f.parameters)

    assert (
        res
        == "a: int, b: int = 1, *args: list\\[str\\], *, c: int, d: int, **kwargs: dict\\[str, str\\]"
    )