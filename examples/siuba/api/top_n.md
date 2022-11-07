# top_n

`top_n(__data, n, wt=None)`

Filter to keep the top or bottom entries in each group.

## Parameters

| Name      | Type   | Description                                                                        | Default   |
|-----------|--------|------------------------------------------------------------------------------------|-----------|
| `___data` |        | A DataFrame.                                                                       | required  |
| `n`       |        | The number of rows to keep in each group.                                          | required  |
| `wt`      |        | A column or expression that determines ordering (defaults to last column in data). | `None`    |

## Examples

```python
>>> from siuba import _, top_n
>>> df = pd.DataFrame({'x': [3, 1, 2, 4], 'y': [1, 1, 0, 0]})
>>> top_n(df, 2, _.x)
   x  y
0  3  1
3  4  0
```

```python
>>> top_n(df, -2, _.x)
   x  y
1  1  1
2  2  0
```

```python
>>> top_n(df, 2, _.x*_.y)
   x  y
0  3  1
1  1  1
```