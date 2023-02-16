import quartodoc.ast as qast
import pytest

from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc
from griffe.docstrings.parsers import parse_numpy

from quartodoc import get_object


@pytest.mark.parametrize(
    "el, body",
    [
        ("See Also\n---", ""),
        ("See Also\n---\n", ""),
        ("See Also\n--------", ""),
        ("\n\nSee Also\n---\n", ""),
        ("See Also\n---\nbody text", "body text"),
        ("See Also\n---\nbody text", "body text"),
    ],
)
def test_transform_docstring_section(el, body):
    src = ds.DocstringSectionText(el, title=None)
    res = qast._DocstringSectionPatched.transform(src)

    assert isinstance(res, qast.DocstringSectionSeeAlso)
    assert res.value == body


@pytest.mark.parametrize(
    "el, cls",
    [
        ("See Also\n---", qast.DocstringSectionSeeAlso),
        ("Warnings\n---", qast.DocstringSectionWarnings),
        ("Notes\n---", qast.DocstringSectionNotes),
    ],
)
def test_transform_docstring_section_subtype(el, cls):
    # using transform method ----
    src = ds.DocstringSectionText(el, title=None)
    res = qast._DocstringSectionPatched.transform(src)

    assert isinstance(res, cls)

    # using transform function ----
    parsed = parse_numpy(dc.Docstring(el))
    assert len(parsed) == 1

    res2 = qast.transform(parsed[0])
    assert isinstance(res2, cls)


@pytest.mark.xfail(reason="TODO: sections get grouped into single element")
def test_transform_docstring_section_clump():
    docstring = "See Also---\n\nWarnings\n---\n\nNotes---\n\n"
    parsed = parse_numpy(dc.Docstring(docstring))

    assert len(parsed) == 1

    # res = transform(parsed[0])

    # what to do here? this should more reasonably be handled when transform
    # operates on the root.


def test_preview_no_fail(capsys):
    qast.preview(get_object("quartodoc", "get_object"))

    res = capsys.readouterr()

    assert "get_object" in res.out
