import quartodoc.ast as qast
import pytest

from quartodoc._griffe_compat import docstrings as ds
from quartodoc._griffe_compat import dataclasses as dc
from quartodoc._griffe_compat import parse_numpy

from quartodoc import get_object


@pytest.mark.parametrize(
    "el, body",
    [
        ("See Also\n---", ""),
        ("See Also\n---\n", ""),
        ("See Also\n--------", ""),
        ("See Also\n---\nbody text", "body text"),
        ("See Also\n---\nbody text", "body text"),
    ],
)
def test_transform_docstring_section(el, body):
    src = ds.DocstringSectionText(el, title=None)
    res = qast._DocstringSectionPatched.transform(src)

    assert len(res) == 1
    assert isinstance(res[0], qast.DocstringSectionSeeAlso)
    assert res[0].title == "See Also"
    assert res[0].value == body


def test_transform_docstring_section_multiple():
    # Note the starting text is not a section header
    # so this should be split into two sections: short description, and see also.
    src = ds.DocstringSectionText("A short description\n\nSee Also\n---\n")
    res = qast._DocstringSectionPatched.transform(src)

    assert len(res) == 2
    assert res[0].value == "A short description\n\n"
    assert isinstance(res[1], qast.DocstringSectionSeeAlso)
    assert res[1].title == "See Also"
    assert res[1].value == ""


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

    assert len(res) == 1
    assert isinstance(res[0], cls)

    # using transform function ----
    parsed = parse_numpy(dc.Docstring(el))
    assert len(parsed) == 1

    res2 = qast.transform(parsed)
    assert len(res2) == 1
    assert isinstance(res2[0], cls)


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


@pytest.mark.xfail
def test_preview_warn_alias_no_load():
    # fetch an alias to pydantic.BaseModel, without loading pydantic
    # attempting to get alias.target will fail, but preview should still work.
    obj = get_object("quartodoc.ast.BaseModel", load_aliases=False)
    with pytest.warns(UserWarning) as record:
        qast.preview(obj)

    msg = record[0].message.args[0]
    assert (
        "Could not resolve Alias target `quartodoc._pydantic_compat.BaseModel`" in msg
    )


@pytest.mark.parametrize(
    "text, dst",
    [("One\n---\nab\n\nTwo\n---\n\ncd", [("One", "ab\n\n"), ("Two", "\ncd")])],
)
def test_transform_split_sections(text, dst):
    res = qast._DocstringSectionPatched.split_sections(text)
    assert res == dst
