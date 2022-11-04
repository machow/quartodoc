
# quartodoc

Generate python API documentation for quarto.

## Install

## Basic use

``` python
from quartodoc import get_function, MdRenderer

# get function object ---
f_obj = get_function("quartodoc", "get_function")

# render ---
renderer = MdRenderer(header_level = 1)
print(
    renderer.to_md(f_obj)
)
```

    # get_function

    get_function(module: str, func_name: str, parser: str = 'numpy')

    Fetch a function.

    | Name        | Type   | Description                | Default   |
    |-------------|--------|----------------------------|-----------|
    | `module`    | str    | A module name.             | required  |
    | `func_name` | str    | A function name.           | required  |
    | `parser`    | str    | A docstring parser to use. | `'numpy'` |

    ```python
    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

\`\`\`
