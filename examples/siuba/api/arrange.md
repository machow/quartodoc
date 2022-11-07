# arrange

`arrange(__data, *args)`

Re-order the rows of a DataFrame using the values of specified columns.

## Parameters

| Name     | Type   | Description                                   | Default   |
|----------|--------|-----------------------------------------------|-----------|
| `__data` |        | The input table.                              | required  |
| `*args`  |        | Columns or expressions used to sort the rows. | `()`      |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, arrange, mutate
```

```python
>>> df = pd.DataFrame({"x": [2, 1, 1], "y": ["aa", "b", "aa"]})
>>> df
   x   y
0  2  aa
1  1   b
2  1  aa
```

Arrange sorts on the first argument, then the second, etc..

```python
>>> df >> arrange(_.x, _.y)
   x   y
2  1  aa
1  1   b
0  2  aa
```

Use a minus sign (`-`) to sort is descending order.

```python
>>> df >> arrange(-_.x)
   x   y
0  2  aa
1  1   b
2  1  aa
```

Note that arrange can sort on complex expressions:

```python
>>> df >> arrange(-_.y.str.len())
   x   y
0  2  aa
2  1  aa
1  1   b
```

The case above is equivalent to running a mutate before arrange:

```python
>>> df >> mutate(res = -_.y.str.len()) >> arrange(_.res)
   x   y  res
0  2  aa   -2
2  1  aa   -2
1  1   b   -1
```