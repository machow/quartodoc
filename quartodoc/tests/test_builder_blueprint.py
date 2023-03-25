from quartodoc import get_object
from quartodoc import layout as lo
from quartodoc.builder.blueprint import BlueprintTransformer
import pytest

TEST_MOD = "quartodoc.tests.example"


@pytest.fixture
def lay():
    return lo.Layout(
        sections=[
            lo.Section(
                title="",
                desc="",
                contents=[f"{TEST_MOD}.a_func", f"{TEST_MOD}.a_attr"],
            ),
            lo.Section(
                title="",
                desc="",
                contents=[
                    f"{TEST_MOD}.AClass",
                    f"{TEST_MOD}.AClass.a_attr",
                    f"{TEST_MOD}.AClass.a_method",
                ],
            ),
        ]
    )


@pytest.fixture
def bp():
    return BlueprintTransformer()


@pytest.mark.parametrize("path", ["quartodoc.get_object", "quartodoc:get_object"])
def test_blueprint_basic(bp, path):
    auto = lo.Auto(name=path)
    res = bp.visit(auto)

    obj = get_object(path)
    dst = lo.DocFunction(
        name=path, obj=obj, anchor="quartodoc.get_object", kind="function"
    )

    # TODO: it's hard to compare pydantic models with griffe objects in them
    # we likely need to define how to serialize them to json.
    assert str(res) == str(dst)


@pytest.mark.parametrize("dynamic", [False, True])
def test_blueprint_visit_class(bp, dynamic):
    path = "quartodoc.tests.example:AClass"
    auto = lo.Auto(name=path, members=["a_method"], dynamic=dynamic)
    res = bp.visit(auto)

    assert isinstance(res, lo.DocClass)
    assert len(res.members) == 1
    assert res.members[0].name == "a_method"
    assert res.members[0].obj.path == path.replace(":", ".") + ".a_method"


@pytest.mark.parametrize("dynamic", [False, True])
def test_blueprint_visit_module(bp, dynamic):
    path = "quartodoc.tests.example"
    auto = lo.Auto(name=path, members=["a_func"], dynamic=dynamic)
    res = bp.visit(auto)

    assert isinstance(res, lo.DocModule)
    assert len(res.members) == 1
    assert res.members[0].name == "a_func"
    assert res.members[0].obj.path == path.replace(":", ".") + ".a_func"
