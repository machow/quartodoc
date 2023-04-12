def no_annotations(a, b=1, *args, c, d=2, **kwargs):
    """A function with a signature"""


def yes_annotations(
    a: int, b: int = 1, *args: list[str], c: int, d: int, **kwargs: dict[str, str]
):
    """A function with a signature"""
