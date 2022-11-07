# spread

`spread(__data, key, value, fill=None, reset_index=True)`

Reshape table by spreading it out to wide format.

## Parameters

| Name     | Type   | Description                                                                   | Default   |
|----------|--------|-------------------------------------------------------------------------------|-----------|
| `__data` |        | The input data.                                                               | required  |
| `key`    |        | Column whose values will be used as new column names.                         | required  |
| `value`  |        | Column whose values will fill the new column entries.                         | required  |
| `fill`   |        | Value to set for any missing values. By default keeps them as missing values. | `None`    |

## Examples

```python
>>> import pandas as pd                                                
>>> from siuba import _, gather                                        
```

```python
>>> df = pd.DataFrame({"id": ["a", "b"], "x": [1, 2], "y": [3, None]}) 
```

```python
>>> long = gather(df, "key", "value", -_.id, drop_na=True)
>>> long
  id key  value
0  a   x    1.0
1  b   x    2.0
2  a   y    3.0
```

```python
>>> spread(long, "key", "value")
  id    x    y
0  a  1.0  3.0
1  b  2.0  NaN
```