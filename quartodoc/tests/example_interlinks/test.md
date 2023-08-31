
## `` [](`quartodoc.layout`) ``

output: [`quartodoc.layout`](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[](`quartodoc.layout`)'
    ├─output_text = 'quartodoc.layout'
    └─output_link = '/api/layout.html#quartodoc.layout'

## `` [](`quartodoc.MdRenderer`) ``

output:
[`quartodoc.MdRenderer`](/api/MdRenderer.html#quartodoc.MdRenderer)

    █─TestSpecEntry
    ├─input = '[](`quartodoc.MdRenderer`)'
    ├─output_text = 'quartodoc.MdRenderer'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer'

## `` [](`quartodoc.MdRenderer.render`) ``

output:
[`quartodoc.MdRenderer.render`](/api/MdRenderer.html#quartodoc.MdRenderer.render)

    █─TestSpecEntry
    ├─input = '[](`quartodoc.MdRenderer.render`)'
    ├─output_text = 'quartodoc.MdRenderer.render'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer.render'

## `` [](`quartodoc.MdRenderer.style`) ``

output:
[`quartodoc.MdRenderer.style`](/api/MdRenderer.html#quartodoc.MdRenderer.style)

    █─TestSpecEntry
    ├─input = '[](`quartodoc.MdRenderer.style`)'
    ├─output_text = 'quartodoc.MdRenderer.style'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer.style'

## `` [](`quartodoc.layout) ``

output: ``

    █─TestSpecEntry
    ├─input = '[](`quartodoc.layout)'
    └─error = 'RefSyntaxError'

## `[](http://example.com)`

output: [](http://example.com)

    █─TestSpecEntry
    ├─input = '[](http://example.com)'
    └─output_element = █─Unchanged
                       └─content = 'http://example.com'

## `` [some explanation](`quartodoc.layout`) ``

output: [some explanation](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[some explanation](`quartodoc.layout`)'
    ├─output_text = 'some explanation'
    └─output_link = '/api/layout.html#quartodoc.layout'

## `` [](`quartodoc.layout`) ``

output: [`quartodoc.layout`](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[](`quartodoc.layout`)'
    ├─output_text = 'quartodoc.layout'
    └─output_link = '/api/layout.html#quartodoc.layout'

## `` [](`~quartodoc.layout`) ``

output: [`layout`](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[](`~quartodoc.layout`)'
    └─output_text = 'layout'

## `` [](:function:`quartodoc.MdRenderer.render`) ``

output:
[`quartodoc.MdRenderer.render`](/api/MdRenderer.html#quartodoc.MdRenderer.render)

    █─TestSpecEntry
    ├─input = '[](:function:`quartodoc.MdRenderer.render`)'
    ├─output_text = 'quartodoc.MdRenderer.render'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer.render'

## `` [](:func:`quartodoc.MdRenderer.render`) ``

output:
[`quartodoc.MdRenderer.render`](/api/MdRenderer.html#quartodoc.MdRenderer.render)

    █─TestSpecEntry
    ├─input = '[](:func:`quartodoc.MdRenderer.render`)'
    ├─output_text = 'quartodoc.MdRenderer.render'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer.render'

## `` [](:attribute:`quartodoc.MdRenderer.style`) ``

output:
[`quartodoc.MdRenderer.style`](/api/MdRenderer.html#quartodoc.MdRenderer.style)

    █─TestSpecEntry
    ├─input = '[](:attribute:`quartodoc.MdRenderer.style`)'
    ├─output_text = 'quartodoc.MdRenderer.style'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer.style'

## `` [](:class:`quartodoc.MdRenderer`) ``

output:
[`quartodoc.MdRenderer`](/api/MdRenderer.html#quartodoc.MdRenderer)

    █─TestSpecEntry
    ├─input = '[](:class:`quartodoc.MdRenderer`)'
    ├─output_text = 'quartodoc.MdRenderer'
    └─output_link = '/api/MdRenderer.html#quartodoc.MdRenderer'

## `` [](:module:`quartodoc.layout`) ``

output: [`quartodoc.layout`](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[](:module:`quartodoc.layout`)'
    ├─output_text = 'quartodoc.layout'
    └─output_link = '/api/layout.html#quartodoc.layout'

## `` [](:py:module:`quartodoc.layout`) ``

output: [`quartodoc.layout`](/api/layout.html#quartodoc.layout)

    █─TestSpecEntry
    ├─input = '[](:py:module:`quartodoc.layout`)'
    ├─output_text = 'quartodoc.layout'
    └─output_link = '/api/layout.html#quartodoc.layout'

## `` [](:external+other:py:function:`quartodoc.get_object`) ``

output:
[`quartodoc.get_object`](other+api/get_object.html#quartodoc.get_object)

    █─TestSpecEntry
    ├─input = '[](:external+other:py:function:`quartodoc.get_obj ...
    ├─output_text = 'quartodoc.get_object'
    └─output_link = 'other+api/get_object.html#quartodoc.get_object'

## `` [](:external+other:`quartodoc.layout`) ``

output: `quartodoc.layout`

    █─TestSpecEntry
    ├─input = '[](:external+other:`quartodoc.layout`)'
    ├─output_element = █─Code
    │                  └─content = ':external+other:`quartodoc.layout`'
    └─warning = 'InvLookupError'

## `` [](:attribute:`quartodoc.MdRenderer.render`) ``

output: `quartodoc.MdRenderer.render`

    █─TestSpecEntry
    ├─input = '[](:attribute:`quartodoc.MdRenderer.render`)'
    └─warning = 'InvLookupError'

## `` [](:mod:`quartodoc.layout`) ``

output: `quartodoc.layout`

    █─TestSpecEntry
    ├─input = '[](:mod:`quartodoc.layout`)'
    └─warning = 'InvLookupError'
