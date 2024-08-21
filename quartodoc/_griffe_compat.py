# flake8: noqa

try:
    from griffe import GriffeLoader
    from griffe import ModulesCollection, LinesCollection

    import _griffe.models as dataclasses
    import _griffe.docstrings.models as docstrings
    import _griffe.expressions as expressions

    from griffe import Parser, parse, parse_numpy
    from griffe import AliasResolutionError
except ImportError:
    from griffe.loader import GriffeLoader
    from griffe.collections import ModulesCollection, LinesCollection

    import griffe.dataclasses as dataclasses
    import griffe.docstrings.dataclasses as docstrings
    import griffe.expressions as expressions

    from griffe.docstrings.parsers import Parser, parse
    from griffe.exceptions import AliasResolutionError
