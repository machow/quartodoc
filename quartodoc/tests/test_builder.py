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


def test_blueprint(lay):
    BlueprintTransformer
