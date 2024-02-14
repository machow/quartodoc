from quartodoc.tests.example_alias_target__nested import (  # noqa: F401
    nested_alias_target,
    NestedClass as ClassAlias,
    tabulate as external_alias,
)


def alias_target():
    """An alias target"""


class AClass:
    some_method = nested_alias_target
