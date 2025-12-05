"""Module with comprehensive numpydoc examples."""


def full_numpydoc_function(x, y=None, *args, option=False, **kwargs):
    """A one-line summary.

    An extended summary that provides more detail about what this
    function does. This demonstrates the full range of numpydoc
    sections that are supported.

    Parameters
    ----------
    x : int
        The first parameter.
    y : str, optional
        The second parameter.
    *args : float
        Variable positional arguments.
    option : bool, default False
        A keyword-only parameter.
    **kwargs : dict
        Variable keyword arguments.

    Returns
    -------
    result : int
        The computed result with name and type.
    list
        A secondary return value with only type.

    Yields
    ------
    value : str
        Generated string values.

    Raises
    ------
    ValueError
        If x is negative.
    TypeError
        If y is not a string.

    See Also
    --------
    other_function : Related functionality.
    module.another_function : Another related function.

    Notes
    -----
    I am a note.

    References
    ----------
    .. [1] Author Name, "Paper Title", Journal, 2024. TODO

    Examples
    --------
    Basic usage:

    >>> full_numpydoc_function(1, "test")
    (42, [1, 2, 3])

    With optional parameters:

    >>> full_numpydoc_function(1, option=True)
    (42, [])
    """
    pass
