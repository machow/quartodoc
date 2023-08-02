import copy
import pytest

from quartodoc.autosummary import Builder

EXAMPLE_SECTIONS = [
    {
        "title": "Preperation Functions",
        "desc": "Functions that fetch objects.\nThey prepare a representation of the site.\n",
        "contents": ["Auto", "blueprint", "collect", "get_object", "preview"],
    },
    {
        "title": "Docstring Renderers",
        "desc": "Renderers convert parsed docstrings into a target format, like markdown.\n",
        "contents": [
            {"name": "MdRenderer", "children": "linked"},
            {"name": "MdRenderer.render", "dynamic": True},
            {"name": "MdRenderer.render_annotation", "dynamic": True},
            {"name": "MdRenderer.render_header", "dynamic": True},
        ],
    },
    {
        "title": "API Builders",
        "desc": "Builders build documentation. They tie all the pieces\nof quartodoc together.\n",
        "contents": [
            {"kind": "auto", "name": "Builder", "members": []},
            "Builder.from_quarto_config",
            "Builder.build",
            "Builder.write_index",
        ],
    },
]


@pytest.fixture
def sections():
    return copy.deepcopy(EXAMPLE_SECTIONS)


def check_ValueError(sections):
    "Check that a ValueError is raised when creating a `Builder` instance. Return the error message as a string."
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package="quartodoc")
    return str(e.value)


def test_valid_yaml(sections):
    "Test that valid YAML passes validation"
    Builder(sections=sections, package="quartodoc")


def test_missing_name_contents_1(sections):
    "Test that a missing name in contents raises an error"
    del sections[2]["contents"][0]["name"]
    msg = check_ValueError(sections)
    assert (
        "- Missing field `name` for element 0 in the list for `contents` located in element 2 in the list for `sections`"
        in msg
    )


def test_missing_name_contents_2(sections):
    "Test that a missing name in contents raises an error in a different section."
    del sections[1]["contents"][0]["name"]
    msg = check_ValueError(sections)
    assert (
        "- Missing field `name` for element 0 in the list for `contents` located in element 1 in the list for `sections`"
        in msg
    )


def test_misplaced_kindpage(sections):
    "Test that a misplaced kind: page raises an error"
    sections[0]["kind"] = "page"
    msg = check_ValueError(sections)
    assert (
        " - Missing field `path` for element 0 in the list for `sections`, which you need when setting `kind: page`."
        in msg
    )
