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


def test_builder_no_title_no_topmatter(tmp_path):
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      title: null
      sections:
        - title: first section
          contents: [a_func]
    """
    )

    builder = Builder.from_quarto_config(cfg)
    builder.dir = str(tmp_path)
    bp = blueprint(builder.layout)
    builder.write_index(bp)

    index = (Path(tmp_path) / "index.qmd").read_text()
    assert not index.startswith("---")


def test_builder_index_topmatter_custom(tmp_path):
    """Test that index_topmatter allows custom frontmatter."""
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      title: "This will be ignored"
      index-topmatter:
        title: "Custom API Reference"
        description: "API documentation for my package"
        author: "Test Author"
        date: "2024-01-01"
      sections:
        - title: first section
          contents: [a_func]
    """
    )

    builder = Builder.from_quarto_config(cfg)
    builder.dir = str(tmp_path)
    bp = blueprint(builder.layout)
    builder.write_index(bp)

    index = (Path(tmp_path) / "index.qmd").read_text()
    assert index.startswith("---")
    assert "title: Custom API Reference" in index
    assert "description: API documentation for my package" in index
    assert "author: Test Author" in index
    assert "This will be ignored" not in index  # Original title not used


def test_builder_index_topmatter_empty(tmp_path):
    """Test that empty index_topmatter generates empty frontmatter."""
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      title: "Will be ignored"
      index-topmatter: {}
      sections:
        - title: first section
          contents: [a_func]
    """
    )

    builder = Builder.from_quarto_config(cfg)
    builder.dir = str(tmp_path)
    bp = blueprint(builder.layout)
    builder.write_index(bp)

    index = (Path(tmp_path) / "index.qmd").read_text()
    assert index.startswith("---\n{}\n\n---")  # Empty dict rendered as {} in YAML


def test_builder_index_topmatter_fallback(tmp_path):
    """Test that title is used when index_topmatter is not provided."""
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      title: "Function Reference"
      sections:
        - title: first section
          contents: [a_func]
    """
    )

    builder = Builder.from_quarto_config(cfg)
    builder.dir = str(tmp_path)
    bp = blueprint(builder.layout)
    builder.write_index(bp)

    index = (Path(tmp_path) / "index.qmd").read_text()
    assert "title: Function Reference" in index


def test_builder_index_topmatter_full_build(tmp_path):
    """Test full build with index-topmatter configuration."""
    cfg = yaml.safe_load(
        """
    quartodoc:
      package: quartodoc.tests.example
      index-topmatter:
        title: "Complete API Reference"
        description: "Full documentation with custom frontmatter"
        author: "Test Suite"
        date-modified: "2024-12-04"
        toc: true
        toc-depth: 2
      sections:
        - title: Test Functions
          desc: "Testing the new index-topmatter feature"
          contents:
            - a_func
            - AClass
    """
    )

    builder = Builder.from_quarto_config(cfg)
    builder.dir = str(tmp_path / "api")

    # Run the full build
    builder.build()

    # Check that the index file was created with correct frontmatter
    index_path = Path(tmp_path) / "api" / "index.qmd"
    assert index_path.exists()

    index_content = index_path.read_text()
    assert "title: Complete API Reference" in index_content
    assert "description: Full documentation with custom frontmatter" in index_content
    assert "author: Test Suite" in index_content
    assert "date-modified: '2024-12-04'" in index_content or "date-modified: 2024-12-04" in index_content
    assert "toc: true" in index_content
    assert "toc-depth: 2" in index_content

    # Check that the section title is still rendered correctly
    assert "## Test Functions" in index_content
    assert "Testing the new index-topmatter feature" in index_content

    # Check that individual pages were created
    assert (Path(tmp_path) / "api" / "a_func.qmd").exists()
    assert (Path(tmp_path) / "api" / "AClass.qmd").exists()
