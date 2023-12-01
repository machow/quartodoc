from functools import partial

NOTE = "Notes\n----\nI am a note"


a: int
"""The a module attribute"""

b: str = "2"
"""The b module attribute"""


def f(a, b, c):
    """Return something

    {note}
    """


f.__doc__ = f.__doc__.format(note=NOTE)


class AClass:
    def simple(self, x):
        """A simple method"""

    def dynamic_doc(self, x):
        ...

    dynamic_doc.__doc__ = """A dynamic method"""

    # note that we could use the partialmethod, but I am not sure how to
    # correctly set its __doc__ attribute in that case.
    dynamic_create = partial(dynamic_doc, x=1)
    dynamic_create.__doc__ = dynamic_doc.__doc__


class InstanceAttrs:
    """Some InstanceAttrs class"""

    z: int
    """The z attribute"""

    def __init__(self, a: int, b: str):
        self.a = a
        self.b = b
        """The b attribute"""


some_instance = InstanceAttrs(1, 1)
some_instance.__doc__ = "Dynamic instance doc"
