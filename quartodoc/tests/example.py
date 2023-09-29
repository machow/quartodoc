"""A module"""

# flake8: noqa

from quartodoc.tests.example_alias_target import (
    alias_target as a_alias,
    nested_alias_target as a_nested_alias,
)


def a_func():
    """A function"""


a_attr = 1
"""An attribute"""


class AClass:
    """A class"""

    a_attr = 1
    """A class attribute"""

    def a_method():
        """A method"""
