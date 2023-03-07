NOTE = "Notes\n----\nI am a note"


def f(a, b, c):
    """Return something

    {note}
    """


f.__doc__ = f.__doc__.format(note=NOTE)
