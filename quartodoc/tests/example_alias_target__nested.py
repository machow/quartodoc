"""
This function gets imported in example_alias_target, and from there imported into example.
"""

from tabulate import tabulate  # noqa: F401


def nested_alias_target():
    """A nested alias target"""


class Parent:
    def parent_method(self):
        """p1 method"""


class NestedClass(Parent):
    def f(self):
        """a method"""

    manually_attached = nested_alias_target
