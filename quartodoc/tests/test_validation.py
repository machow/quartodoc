import pytest, copy
from quartodoc.autosummary import Builder

EXAMPLE_SECTIONS = [
                  {'title':  'Preperation Functions',
                   'desc': 'These functions fetch and analyze python objects, including parsing docstrings.\nThey prepare a basic representation of your doc site that can be rendered and built.\n', 
                   'contents': ['Auto', 'blueprint', 'collect', 'get_object', 'preview']}, 
                  {'title': 'Docstring Renderers', 
                   'desc': 'Renderers convert parsed docstrings into a target format, like markdown.\n', 
                   'contents': [{'name': 'MdRenderer', 'children': 'linked'}, 
                                {'name': 'MdRenderer.render', 'dynamic': True}, 
                                {'name': 'MdRenderer.render_annotation', 'dynamic': True}, 
                                {'name': 'MdRenderer.render_header', 'dynamic': True}, 
                                {'name': 'MdRenderer.signature', 'dynamic': True}, 
                                {'name': 'MdRenderer.summarize', 'dynamic': True}]
                    }, 
                    {'title': 'API Builders', 
                        'desc': 'Builders are responsible for building documentation. They tie all the pieces\nof quartodoc together, and can be defined in your _quarto.yml config.\n', 
                        'contents': [{'kind': 'auto', 'name': 'Builder', 'members': []}, 
                                    'Builder.from_quarto_config', 'Builder.build', 'Builder.write_index', 'Builder.write_doc_pages', 'Builder.write_sidebar', 'Builder.create_inventory']
                    },
                ]

@pytest.fixture
def sections():
    return copy.deepcopy(EXAMPLE_SECTIONS)

def test_valid_yaml(sections):
    "Test that valid YAML passes validation"
    Builder(sections=sections, package='quartodoc')

def test_missing_title(sections):
    "Test that missing title raises an error"
    del sections[0]['title']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `title` for element 0 in the list for `sections`' in str(e.value)

def test_missing_desc(sections):
    "Test that a missing description raises an error"
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    del sections[2]['desc']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `desc` for element 2 in the list for `sections`' in str(e.value)

def test_missing_name_contents_1(sections):
    "Test that a missing name in contents raises an error"
    del sections[2]['contents'][0]['name']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `name` for element 0 in the list for `contents` located in element 2 in the list for `sections`' in str(e.value)

def test_missing_name_contents_2(sections):
    "Test that a missing name in contents raises an error in a different section."
    del sections[1]['contents'][0]['name']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `name` for element 0 in the list for `contents` located in element 1 in the list for `sections`' in str(e.value)

def test_misplaced_kindpage(sections):
    "Test that a misplaced kind: page raises an error"
    sections[0]['kind'] = 'page'
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert ' - Missing field `path` for element 0 in the list for `sections`, which you need when setting `kind: page`.' in str(e.value)
