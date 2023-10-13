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


def test_missing_name_contents(snapshot):
    "Test that a missing name in contents raises an error in a different section."

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - title: Section 1
        - title: Section 2
          contents:

            # name missing here ----
            - children: linked

            - name: MdRenderer
    """

    msg = check_ValueError(cfg)
    assert msg == snapshot


def test_misplaced_kindpage(snapshot):
    "Test that a misplaced kind: page raises an error"

    cfg = """
    quartodoc:
      package: zzz
      sections:
        - kind: page

    """

    msg = check_ValueError(cfg)
    assert msg == snapshot
