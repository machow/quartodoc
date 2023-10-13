import pytest

from quartodoc.layout import Layout, Page, Text, Section  # noqa

from quartodoc._pydantic_compat import ValidationError


@pytest.mark.parametrize(
    "cfg, res",
    [
        (
            {"kind": "page", "package": "abc", "path": "xyz", "contents": []},
            Page(package="abc", path="xyz", contents=[]),
        ),
        (
            {
                "kind": "page",
                "package": "abc",
                "path": "xyz",
                "contents": [{"kind": "text", "contents": "abc"}],
            },
            Page(package="abc", path="xyz", contents=[Text(contents="abc")]),
        ),
    ],
)
def test_layout_from_config(cfg, res):
    page = Page(**cfg)
    assert page == res

    layout = Layout(sections=[cfg])
    assert layout.sections[0] == res


@pytest.mark.parametrize(
    "kwargs, msg_part",
    [
        ({}, "must specify a title, subtitle, or contents field"),
        ({"title": "x", "subtitle": "y"}, "cannot specify both"),
    ],
)
def test_section_validation_fails(kwargs, msg_part):
    with pytest.raises(ValueError) as exc_info:
        Section(**kwargs)

    assert msg_part in exc_info.value.args[0]


def test_layout_extra_forbidden():
    with pytest.raises(ValidationError) as exc_info:
        Section(title="abc", desc="xyz", contents=[], zzzzz=1)

    assert "extra fields not permitted" in str(exc_info.value)
