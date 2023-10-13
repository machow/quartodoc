import pytest
import yaml

from textwrap import indent, dedent

from quartodoc.autosummary import Builder


def check_ValueError(cfg: str):
    "Check that a ValueError is raised when creating a `Builder` instance. Return the error message as a string."

    d = yaml.safe_load(cfg)
    with pytest.raises(ValueError) as e:
        Builder.from_quarto_config(d)

    fmt_cfg = indent(dedent(cfg), " " * 4)
    fmt_value = indent(str(e.value), " " * 4)
    return f"""\
Code:\n{fmt_cfg}
Error:\n{fmt_value}
"""


@pytest.mark.skip("title is now optional")
def test_missing_title():
    "Test that missing title raises an error"

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - desc: "abc"
          contents:
            - get_object
    """

    check_ValueError(cfg)
    # assert "- Missing field `title` for element 0 in the list for `sections`" in msg


@pytest.mark.skip("desc is now optional")
def test_missing_desc():
    "Test that a missing description raises an error"

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - title: "A section"
          contents:
            - get_object
    """

    check_ValueError(cfg)
    # assert "- Missing field `desc` for element 2 in the list for `sections`" in msg


@pytest.mark.skip("contents is now optional")
def test_missing_name_contents_1():
    "Test that a missing name in contents raises an error"

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - title: "A section"
          contents:
            - get_object
    """

    check_ValueError(cfg)
    # assert (
    #     "- Missing field `name` for element 0 in the list for `contents` located in element 2 in the list for `sections`"
    #     in msg
    # )


def test_missing_name_contents_2(snapshot):
    "Test that a missing name in contents raises an error in a different section."

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - title: Section 1
        - title: Section 2
          contents:
            - children: linked
            - name: MdRenderer
    """

    msg = check_ValueError(cfg)
    assert msg == snapshot
    # assert (
    #     "- Missing field `name` for element 0 in the list for `contents` located in element 1 in the list for `sections`"
    #     in msg
    # )


def test_misplaced_kindpage(snapshot):
    "Test that a misplaced kind: page raises an error"

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - kind: page

    """

    # the challenge with the pydantic feedback here is that, since Section now does
    # not need to have title, desc, or contents. It believes the `kind: page` is a
    # screwed up section :/.
    # It seems like we need to intercept any error where kind is specified, and
    # customize our message (e.g. we know kind: "page" indicates someone is trying
    # to specify a Page)
    msg = check_ValueError(cfg)
    assert msg == snapshot

    # sections[0]["kind"] = "page"
    # msg = check_ValueError(sections)
    # assert (
    #     " - Missing field `path` for element 0 in the list for `sections`, which you need when setting `kind: page`."
    #     in msg
    # )
