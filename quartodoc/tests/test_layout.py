import pytest

from quartodoc.layout import Layout, Page, Text, Section  # noqa


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
