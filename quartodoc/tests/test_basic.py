import pytest

from quartodoc import get_object, get_function, MdRenderer
from quartodoc._griffe_compat import docstrings as ds
from quartodoc._griffe_compat import dataclasses as dc

# TODO: rename to test_autosummary (or refactor autosummary into parts)


def test_get_function():
    f_obj = get_function("quartodoc", "get_function")

    assert f_obj.name == "get_function"
    assert any(
        isinstance(x, ds.DocstringSectionExamples) for x in f_obj.docstring.parsed
    )


def test_renderer_render():
    # TODO: use snapshots?
    f_obj = get_function("quartodoc", "get_function")

    renderer = MdRenderer()
    assert isinstance(renderer.render(f_obj), str)


def test_replace_docstring():
    from quartodoc.autosummary import get_object, replace_docstring
    from quartodoc.tests.example_dynamic import f

    obj = get_object("quartodoc", "tests.example_dynamic.f")
    old = obj.docstring

    replace_docstring(obj, f)
    assert obj.docstring is not old

    # just check the end of the piece dynamically added to docstring, since
    # griffe strips the left padding from docstrings.
    assert obj.docstring.value.endswith("I am a note")


def test_attribute_docstring():
    a = get_object("quartodoc", "tests.example_attribute.a")
    assert a.docstring.value == "I am an attribute docstring"


def test_class_attribute_docstring():
    a = get_object("quartodoc", "tests.example_attribute.SomeClass.a")
    assert a.docstring.value == "I am a class attribute docstring"


def test_render_attribute():
    # TODO: snapshot tests
    a = get_object("quartodoc", "tests.example_attribute.a")

    assert MdRenderer().render(a) == "I am an attribute docstring"


def test_get_object_stub_pyi():
    obj = get_object("quartodoc.tests.example_stubs:f")
    assert obj.parameters[0].annotation.name == "int"


def test_get_object_dynamic_module_root():
    obj = get_object("quartodoc", dynamic=True)
    assert isinstance(obj, dc.Module)
    assert obj.path == "quartodoc"


def test_get_object_dynamic_module():
    obj = get_object("quartodoc.renderers", dynamic=True)
    assert isinstance(obj, dc.Module)
    assert obj.path == "quartodoc.renderers"


def test_get_object_dynamic_function():
    obj = get_object("quartodoc.tests.example_dynamic:f", dynamic=True)
    assert obj.docstring.value.endswith("I am a note")


def test_get_object_dynamic_class_method_doc():
    obj = get_object("quartodoc.tests.example_dynamic:AClass", dynamic=True)

    meth = obj.members["dynamic_doc"]
    assert meth.docstring.value == "A dynamic method"


def test_get_object_dynamic_class_method_doc_partial():
    obj = get_object("quartodoc.tests.example_dynamic:AClass", dynamic=True)

    meth = obj.members["dynamic_create"]
    assert meth.docstring.value == "A dynamic method"


def test_get_object_dynamic_class_instance_attr_doc():
    obj = get_object("quartodoc.tests.example_dynamic:InstanceAttrs", dynamic=True)

    assert obj.members["b"].docstring.value == "The b attribute"


@pytest.mark.xfail(reason="The object's docstring (str.__doc__) is currently used :/.")
def test_get_object_dynamic_mod_instance_attr_doc():
    obj = get_object("quartodoc.tests.example_dynamic:b", dynamic=True)

    assert obj.docstring.value == "The b module attribute"


def test_get_object_dynamic_class_instance_attr_doc_class_attr_valueless():
    obj = get_object("quartodoc.tests.example_dynamic:InstanceAttrs", dynamic=True)

    assert obj.members["z"].docstring.value == "The z attribute"


def test_get_object_dynamic_mod_attr_valueless():
    obj = get_object("quartodoc.tests.example_dynamic:a", dynamic=True)

    assert obj.docstring.value == "The a module attribute"


def test_get_object_dynamic_class_attr_valueless():
    obj = get_object("quartodoc.tests.example_dynamic:InstanceAttrs.z", dynamic=True)

    assert obj.docstring.value == "The z attribute"


def test_get_object_dynamic_module_attr_str():
    # a key behavior here is that it does not error attempting to look up
    # str.__module__, which does not exist
    obj = get_object("quartodoc.tests.example_dynamic:NOTE", dynamic=True)

    assert obj.name == "NOTE"

    # this case is weird, but we are dynamically looking up a string
    # so our __doc__ is technically str.__doc__
    assert obj.docstring.value == str.__doc__


def test_get_object_dynamic_module_attr_class_instance():
    # a key behavior here is that it does not error attempting to look up
    # str.__module__, which does not exist
    obj = get_object("quartodoc.tests.example_dynamic:some_instance", dynamic=True)

    assert obj.path == "quartodoc.tests.example_dynamic.some_instance"
    assert obj.docstring.value == "Dynamic instance doc"


def test_get_object_dynamic_class_method_assigned():
    # method is assigned to class using
    # some_method = some_function
    obj = get_object(
        "quartodoc.tests.example_alias_target:AClass.some_method", dynamic=True
    )

    assert isinstance(obj, dc.Alias)
    assert isinstance(obj.target, dc.Function)
    assert (
        obj.target.path
        == "quartodoc.tests.example_alias_target__nested.nested_alias_target"
    )


def test_get_object_dynamic_toplevel_mod_attr(tmp_path):
    """get_object with dynamic=True works for the top-level module's attributes"""
    import sys

    # TODO: should us a context handler
    sys.path.insert(0, str(tmp_path))
    (tmp_path / "some_mod.py").write_text(
        '''
a: int
"""A module attribute"""
'''
    )

    obj = get_object("some_mod:a", dynamic=True)
    assert obj.docstring.value == "A module attribute"

    sys.path.pop(sys.path.index(str(tmp_path)))


@pytest.mark.parametrize(
    "path,dst",
    [
        # No path returned, since it's ambiguous for an instance
        # e.g. class location, vs instance location
        ("quartodoc.tests.example:a_attr", None),
        ("quartodoc.tests.example:AClass.a_attr", None),
        # Functions give their submodule location
        (
            "quartodoc.tests.example:a_alias",
            "quartodoc.tests.example_alias_target:alias_target",
        ),
        (
            "quartodoc.tests.example:a_nested_alias",
            "quartodoc.tests.example_alias_target__nested:nested_alias_target",
        ),
        (
            "quartodoc.tests.example_alias_target:AClass.some_method",
            "quartodoc.tests.example_alias_target__nested:nested_alias_target",
        ),
        # More mundane cases
        ("quartodoc.tests.example", "quartodoc.tests.example"),
        ("quartodoc.tests.example:a_func", "quartodoc.tests.example:a_func"),
        ("quartodoc.tests.example:AClass", "quartodoc.tests.example:AClass"),
        (
            "quartodoc.tests.example:AClass.a_method",
            "quartodoc.tests.example:AClass.a_method",
        ),
    ],
)
def test_func_canonical_path(path, dst):
    import importlib
    from quartodoc.autosummary import _canonical_path

    mod_path, attr_path = path.split(":") if ":" in path else (path, "")

    crnt_part = importlib.import_module(mod_path)

    if attr_path:
        for name in attr_path.split("."):
            crnt_part = getattr(crnt_part, name)

    res = _canonical_path(crnt_part, "")

    assert res == dst
