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
                    {'title': 'Inventory links', 'desc': 'Inventory files map a functions name to its corresponding url in your docs.\nThese functions allow you to create and transform inventory files.\n', 
                     'contents': ['create_inventory', 'convert_inventory']
                    }, 
                    {'title': 'Data models: structural', 
                     'desc': 'Classes for specifying the broad structure your docs.\n', 
                     'contents': [{'kind': 'page', 
                                'path': 'layouts-structure', 
                                'flatten': True, 
                                'contents': ['layout.Layout', 'layout.Section', 'layout.Page', 'layout.ContentElement']}]
                    }, 
                    {'title': 'Data models: docable', 'desc': 'Classes representing python objects to be rendered.\n', 
                     'contents': [{'kind': 'page', 
                                'path': 'layouts-docable', 
                                'flatten': True, 
                                'contents': [{'name': 'layout.Doc', 'members': []}, 'layout.DocFunction', 'layout.DocAttribute', 'layout.DocModule', 'layout.DocClass', 'layout.Link', 'layout.Item', 'layout.ChoicesChildren']}]
                    }, 
                    {'title': 'Data models: docstring patches', 
                     'desc': 'Most of the classes for representing python objects live\nin [](`griffe.dataclasses`) or [](`griffe.docstrings.dataclasses`).\nHowever, the `quartodoc.ast` module has a number of custom classes to fill\nin support for some important docstring sections.\n', 
                     'contents': ['ast.DocstringSectionSeeAlso', 'ast.DocstringSectionNotes', 'ast.DocstringSectionWarnings', 'ast.ExampleCode', 'ast.ExampleText']
                     }
                ]



def test_valid_yaml():
    Builder(sections=EXAMPLE_SECTIONS, package='quartodoc')

def test_missing_title():
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    del sections[0]['title']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `title` for element 0 in the list for `sections`' in str(e.value)


def test_missing_desc():
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    del sections[2]['desc']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `desc` for element 2 in the list for `sections`' in str(e.value)

def test_missing_name_contents_1():
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    del sections[2]['contents'][0]['name']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `name` for element 0 in the list for `contents` located in element 2 in the list for `sections`' in str(e.value)

def test_missing_name_contents_2():
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    del sections[1]['contents'][0]['name']
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert '- Missing field `name` for element 0 in the list for `contents` located in element 1 in the list for `sections`' in str(e.value)

def test_misplaced_kindpage():
    sections = copy.deepcopy(EXAMPLE_SECTIONS)
    sections[0]['kind'] = 'page'
    with pytest.raises(ValueError) as e:
        Builder(sections=sections, package='quartodoc')
    assert ' - Missing field `path` for element 0 in the list for `sections`, which you need when setting `kind: page`.' in str(e.value)
