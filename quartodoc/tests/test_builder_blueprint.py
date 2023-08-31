from quartodoc import get_object
from quartodoc import layout as lo
from quartodoc.builder.blueprint import (
    BlueprintTransformer,
    blueprint,
    WorkaroundKeyError,
)
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


def test_blueprint_default_dynamic(bp):
    from quartodoc.tests.example_dynamic import NOTE

    path = "quartodoc.tests.example_dynamic:f"
    auto = lo.Auto(name=path)

    res = blueprint(auto, dynamic=True)
    assert isinstance(res, lo.DocFunction)
    assert NOTE in res.obj.docstring.value


def test_blueprint_auto_anchor(bp):
    auto = lo.Auto(name="a_func", package="quartodoc.tests.example")
    res = bp.visit(auto)

    assert isinstance(res, lo.DocFunction)
    assert res.name == "a_func"
    assert res.anchor == "quartodoc.tests.example.a_func"


def test_blueprint_lookup_error_message(bp):
    auto = lo.Auto(name="quartodoc.bbb.ccc")

    with pytest.raises(WorkaroundKeyError) as exc_info:
        bp.visit(auto)

    assert (
        "Does an object with the path quartodoc.bbb.ccc exist?"
        in exc_info.value.args[0]
    )


def test_blueprint_auto_package(bp):
    layout = blueprint(lo.Layout(package="quartodoc.tests.example"))
    sections = layout.sections
    assert len(sections) == 1
    assert sections[0].title == "quartodoc.tests.example"
    assert sections[0].desc == "A module"

    # 4 objects documented
    assert len(sections[0].contents) == 4


def test_blueprint_layout_options():
    layout = lo.Layout(
        options={"members": []},
        sections=[
            lo.Section(
                contents=[lo.Auto(name="AClass")],
                package="quartodoc.tests.example",
            )
        ],
    )

    res = blueprint(layout)
    page = res.sections[0].contents[0]
    doc = page.contents[0]

    assert doc.members == []


def test_blueprint_section_options():
    layout = lo.Layout(
        sections=[
            lo.Section(
                contents=[lo.Auto(name="AClass")],
                package="quartodoc.tests.example",
                options={"members": []},
            )
        ]
    )

    res = blueprint(layout)
    page = res.sections[0].contents[0]
    doc = page.contents[0]

    assert doc.members == []


def _check_member_names(members, expected):
    member_names = set([entry.name for entry in members])
    assert member_names == expected


@pytest.mark.parametrize(
    "kind, removed",
    [
        ("attributes", {"some_property", "z", "SOME_ATTRIBUTE"}),
        ("classes", {"D"}),
        ("functions", {"some_method"}),
    ],
)
def test_blueprint_fetch_members_include_kind_false(kind, removed):
    option = {f"include_{kind}": False}
    all_members = {"SOME_ATTRIBUTE", "z", "some_property", "some_method", "D"}

    auto = lo.Auto(name="quartodoc.tests.example_class.C", **option)
    bp = blueprint(auto)
    _check_member_names(bp.members, all_members - removed)


def test_blueprint_fetch_members_include_inherited():
    auto = lo.Auto(name="quartodoc.tests.example_class.Child", include_inherited=True)
    bp = blueprint(auto)

    member_names = set([entry.name for entry in bp.members])
    assert "some_method" in member_names


def test_blueprint_member_options():
    auto = lo.Auto(
        name="quartodoc.tests.example",
        member_options={"signature_path": "short"},
        members=["AClass"],
    )
    bp = blueprint(auto)
    doc_a_class = bp.members[0]

    # member has option set
    assert doc_a_class.signature_path == "short"

    # this currently does not apply to members of members
    assert doc_a_class.members[0].signature_path == "relative"
