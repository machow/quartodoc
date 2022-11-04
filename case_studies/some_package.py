class SomeClass:
    def __init__(self):
        """TODO"""

        pass


def some_function(x: int, *args, **kwargs):
    """Return some thing.

    More about this function.

    Parameters
    ----------
    x: int
        The `x` parameter.
    *args: tuple
        Positional arguments.
    **kwargs: dict, optional
        Keyword arguments.


    Returns
    -------
    int
        A number

    See Also
    --------
    another_function : does something else

    Notes
    -----
    This is a note.

    Examples
    --------

    This is the first example.

    >>> some_function(1)
    2

    This is the seconds example.

    >>> some_function(2)
    3


    """

    return x + 1


def another_function():
    """Another function."""

    pass
