# unnest

`unnest(__data, key='data')`

Unnest a column holding nested data (e.g. Series of lists or DataFrames).

## Parameters

| Name      | Type   | Description                            | Default   |
|-----------|--------|----------------------------------------|-----------|
| `___data` |        | A DataFrame.                           | required  |
| `key`     |        | The name of the column to be unnested. | `'data'`  |

## Examples

```python
>>> import pandas as pd
>>> df = pd.DataFrame({'id': [1,2], 'data': [['a', 'b'], ['c']]})
>>> df >> unnest()
   id data
0   1    a
1   1    b
2   2    c
```