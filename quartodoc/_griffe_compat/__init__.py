# flake8: noqa

try:
    from griffe import GriffeLoader
    from griffe import ModulesCollection, LinesCollection

    from . import dataclasses
    from . import docstrings
    from . import expressions

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
