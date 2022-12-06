# get_object {#sec-get_object}

`get_object(module: str, object_name: str, parser: str = 'numpy')`

Fetch a griffe object.

## Parameters

| Name          | Type   | Description                | Default   |
|---------------|--------|----------------------------|-----------|
| `module`      | str    | A module name.             | required  |
| `object_name` | str    | A function name.           | required  |
| `parser`      | str    | A docstring parser to use. | `'numpy'` |

See Also
--------
get_function: a deprecated function.

## Examples

```python
>>> get_function("quartodoc", "get_function")
<Function('get_function', ...
```

# create_inventory {#sec-create_inventory}

`create_inventory(project: str, version: str, items: list[dc.Object | dc.Alias], uri: str | Callable[dc.Object, str] = <function <lambda> at 0x105878700>, dispname: str | Callable[dc.Object, str] = '-')`

Return a sphinx inventory file.

## Parameters

| Name       | Type                           | Description                                                    | Default                              |
|------------|--------------------------------|----------------------------------------------------------------|--------------------------------------|
| `project`  | str                            | Name of the project (often the package name).                  | required                             |
| `version`  | str                            | Version of the project (often the package version).            | required                             |
| `items`    | list[dc.Object | dc.Alias]     | A docstring parser to use.                                     | required                             |
| `uri`      | str | Callable[dc.Object, str] | Link relative to the docs where the items documentation lives. | `<function <lambda> at 0x105878700>` |
| `dispname` | str | Callable[dc.Object, str] | Name to be shown when a link to the item is made.              | `'-'`                                |

## Examples

```python
>>> f_obj = get_object("quartodoc", "create_inventory")
>>> inv = create_inventory("example", "0.0", [f_obj])
>>> inv
Inventory(project='example', version='0.0', source_type=<SourceTypes.Manual: 'manual'>)
```

To preview the inventory, we can convert it to a dictionary:

```python
>>> _to_clean_dict(inv)
{'project': 'example',
 'version': '0.0',
 'count': 1,
 'items': [{'name': 'quartodoc.create_inventory',
   'domain': 'py',
   'role': 'function',
   'priority': '1',
   'uri': 'quartodoc.create_inventory.html',
   'dispname': '-'}]}
```

# convert_inventory {#sec-convert_inventory}

`convert_inventory(in_name: Union[str, soi.Inventory], out_name=None)`

Convert a sphinx inventory file to json.

## Parameters

| Name       | Type                      | Description             | Default   |
|------------|---------------------------|-------------------------|-----------|
| `in_name`  | Union[str, soi.Inventory] | Name of inventory file. | required  |
| `out_name` |                           | Output file name.       | `None`    |

# MdRenderer {#sec-MdRenderer}

`MdRenderer(self, header_level: int = 2, show_signature: bool = True, hook_pre=None)`

Render docstrings to markdown.

## Parameters

| Name             | Type   | Description                                      | Default   |
|------------------|--------|--------------------------------------------------|-----------|
| `header_level`   | int    | The level of the header (e.g. 1 is the biggest). | `2`       |
| `show_signature` | bool   | Whether to show the function signature.          | `True`    |

## Examples

```python
>>> from quartodoc import MdRenderer, get_object
>>> renderer = MdRenderer(header_level=2)
>>> f = get_object("quartodoc", "get_object")
>>> print(renderer.to_md(f)[:81])
## get_object
`get_object(module: str, object_name: str, parser: str = 'numpy')`
```