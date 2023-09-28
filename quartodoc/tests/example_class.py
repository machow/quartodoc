class C:
    """The short summary.

    The extended summary,
    which may be multiple lines.

    Parameters
    ----------
    x:
        Uses signature type.
    y: int
        Uses manual type.

    """

    SOME_ATTRIBUTE: float
    """An attribute"""

    def __init__(self, x: str, y: int):
        self.x = x
        self.y = y
        self.z: int = 1
        """A documented init attribute"""

    def some_method(self):
        """A method"""

    @property
    def some_property(self):
        """A property"""

    @classmethod
    def some_class_method(cls):
        """A class method"""

    class D:
        """A nested class"""


class Child(C):
    def some_new_method(self):
        """A new method"""


class AttributesTable:
    """The short summary.

    Attributes
    ----------
    x:
        Uses signature type
    y: int
        Uses manual type
    z:
        Defined in init
    """

    x: str
    y: int
    """This docstring should not be used"""

    def __init__(self):
        self.z: float = 1
