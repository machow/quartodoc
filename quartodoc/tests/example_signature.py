import pathlib


def no_annotations(a, b=1, *args, c, d=2, **kwargs):
    """A function with a signature"""


def yes_annotations(
    a: int, b: int = 1, *args: list[str], c: int, d: int, **kwargs: dict[str, str]
):
    """A function with a signature"""


def pos_only(x, /, a, b=2):
    ...


def kw_only(x, *, a, b=2):
    ...


def early_args(x, *args, a, b=2, **kwargs):
    ...


def late_args(x, a, b=2, *args, **kwargs):
    ...


class C:
    ...


def a_complex_signature(x: "list[C | int | None]", y: "pathlib.Pathlib", z):
    """
    Parameters
    ----------
    x:
        The x parameter
    y:
        The y parameter
    z:
        The z parameter (unannotated)
    """
