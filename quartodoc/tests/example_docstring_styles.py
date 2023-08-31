def f_google(a, b: str):
    """A google style docstring.

    Args:
        a (int): The a parameter.
        b: The b parameter.
    """


def f_sphinx(a, b: str):
    """A sphinx style docstring.

    :param a: The a parameter.
    :type a: int
    :param b: The b parameter.
    """


def f_numpy(a, b: str):
    """A numpy style docstring.

    Parameters
    ----------
    a: int
        The a parameter.
    b:
        The b parameter.

    """


# we set an option by default in griffe's numpy parsing
# to allow linebreaks in parameter tables
def f_numpy_with_linebreaks(a, b: str):
    """A numpy style docstring.

    Parameters
    ----------
    a: int
        The a parameter.

    b:
        The b parameter.

    """


def f_quarto_block_in_docstring(a, b: str):
    """A quarto style docstring.

    ```{python}
    1 < 2
    ```
    """
