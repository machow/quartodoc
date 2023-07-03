from __future__ import annotations

import inspect

from sphinx.ext.autodoc import ObjectMember, UNINITIALIZED_ATTR, INSTANCEATTR, SLOTSATTR
from sphinx.pycode import ModuleAnalyzer
from sphinx.util.inspect import safe_getattr

VALUELESS = (UNINITIALIZED_ATTR, INSTANCEATTR, SLOTSATTR)


def is_valueless(obj):
    return object in VALUELESS


def get_module_members(obj, name) -> dict[str, ObjectMember]:
    """Get members of target module."""

    # analyze module for special attribute documentation
    analyzer = ModuleAnalyzer.for_module(obj.__module__)
    analyzer.find_attr_docs()

    attr_docs = analyzer.attr_docs

    members: dict[str, ObjectMember] = {}
    for name in dir(obj):
        try:
            value = safe_getattr(obj, name, None)
            docstring = attr_docs.get(("", name), [])
            members[name] = ObjectMember(name, value, docstring="\n".join(docstring))
        except AttributeError:
            continue

    # annotation only member (ex. attr: int)
    for name in inspect.getannotations(obj):
        if name not in members:
            docstring = attr_docs.get(("", name), [])
            members[name] = ObjectMember(
                name, INSTANCEATTR, docstring="\n".join(docstring)
            )

    return members
