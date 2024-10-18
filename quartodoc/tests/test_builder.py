import pytest
import yaml

from pathlib import Path
from quartodoc import layout as lo
from quartodoc import Builder, blueprint


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


def test_builder_auto_options():
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc
      options:
        members: [a_func, a_attr]
      sections:
        - contents: [quartodoc.tests.example]
    """
    )

    builder = Builder.from_quarto_config(cfg)
    assert builder.layout.options.members == ["a_func", "a_attr"]


def test_builder_generate_sidebar(tmp_path, snapshot):
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      sections:
        - title: first section
          desc: some description
          contents: [a_func]
        - title: second section
          desc: title description
        - subtitle: a subsection
          desc: subtitle description
          contents:
            - a_attr
    """
    )

    builder = Builder.from_quarto_config(cfg)
    bp = blueprint(builder.layout)
    d_sidebar = builder._generate_sidebar(bp)

    assert yaml.dump(d_sidebar) == snapshot


def test_builder_generate_sidebar_options(tmp_path, snapshot):
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      sidebar:
        style: docked
        search: true
        contents:
          - text: "Introduction"
            href: introduction.qmd
          - section: "Reference"
            contents:
             - "{{ contents }}"
          - text: "Basics"
            href: basics-summary.qmd
      sections:
        - title: first section
          desc: some description
          contents: [a_func]
        - title: second section
          desc: title description
        - subtitle: a subsection
          desc: subtitle description
          contents:
            - a_attr
    """
    )

    builder = Builder.from_quarto_config(cfg)
    assert builder.sidebar["file"] == "_quartodoc-sidebar.yml"  # default value

    bp = blueprint(builder.layout)

    d_sidebar = builder._generate_sidebar(bp)
    assert "website" in d_sidebar
    assert "sidebar" in d_sidebar["website"]

    qd_sidebar = d_sidebar["website"]["sidebar"][0]
    assert "file" not in qd_sidebar
    assert qd_sidebar["style"] == "docked"
    assert qd_sidebar["search"]

    assert yaml.dump(d_sidebar) == snapshot
