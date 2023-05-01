import pytest

from pathlib import Path
from quartodoc import layout as lo
from quartodoc import Builder


@pytest.fixture
def builder(tmp_path):
    section = lo.Section(
        title="abc",
        desc="xyz",
        contents=[
            lo.Auto(name="get_object"),
            lo.Auto(
                name="MdRenderer", members=["render", "summarize"], children="separate"
            ),
        ],
    )

    builder = Builder(package="quartodoc", sections=[section], dir=str(tmp_path))

    yield builder


def test_builder_build_filter_simple(builder):
    builder.build(filter="get_object")

    assert (Path(builder.dir) / "get_object.qmd").exists()
    assert not (Path(builder.dir) / "MdRenderer.qmd").exists()


def test_builder_build_filter_wildcard_class(builder):
    builder.build(filter="MdRenderer*")

    len(list(Path(builder.dir).glob("Mdrenderer*"))) == 3


def test_builder_build_filter_wildcard_methods(builder):
    builder.build(filter="MdRenderer.*")

    len(list(Path(builder.dir).glob("Mdrenderer.*"))) == 2
