
# get_function

`get_function(module: str, func_name: str, parser: str = 'numpy')`

Fetch a function.

## Parameters

| Name        | Type | Description                | Default   |
|-------------|------|----------------------------|-----------|
| `module`    | str  | A module name.             | required  |
| `func_name` | str  | A function name.           | required  |
| `parser`    | str  | A docstring parser to use. | `'numpy'` |

## Examples

``` python
>>> get_function("quartodoc", "get_function")
<Function('get_function', ...
```
