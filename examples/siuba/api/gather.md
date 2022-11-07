# gather

`gather(__data, key='key', value='value', *args, drop_na=False, convert=False)`

Reshape table by gathering it in to long format.

## Parameters

| Name      | Type   | Description                                              | Default   |
|-----------|--------|----------------------------------------------------------|-----------|
| `__data`  |        | The input data.                                          | required  |
| `key`     |        | Name of the key (or measure) column, which holds the names of the columns
that were turned into rows.                                                          | `'key'`   |
| `value`   |        | Name of the value column, which holds the values from the columns that
were turned into rows.                                                          | `'value'` |
| `*args`   |        | A selection of columns. If unspecified, all columns are selected. Any
arguments you could pass to the select() verb are allowed.                                                          | `()`      |
| `drop_na` |        | Whether to remove any rows where the value column is NA. | `False`   |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, gather
```

```python
>>> df = pd.DataFrame({"id": ["a", "b"], "x": [1, 2], "y": [3, None]})
```

The code below gathers in all columns, except id:

```python
>>> gather(df, "key", "value", -_.id)
  id key  value
0  a   x    1.0
1  b   x    2.0
2  a   y    3.0
3  b   y    NaN
```

```python
>>> gather(df, "measure", "result", _.x, _.y, drop_na=True)
  id measure  result
0  a       x     1.0
1  b       x     2.0
2  a       y     3.0
```