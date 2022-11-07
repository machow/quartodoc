# anti_join

`anti_join(left, right=None, on=None, *args, by=None)`

Return the left table with every row that would *not* be kept in an inner join.

## Parameters

| Name    | Type   | Description           | Default   |
|---------|--------|-----------------------|-----------|
| `left`  |        | The left-hand table.  | required  |
| `right` |        | The right-hand table. | `None`    |
| `on`    |        | How to match them. By default it uses matches all columns with the same
name across the two tables.                       | `None`    |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, semi_join, anti_join
```

```python
>>> df1 = pd.DataFrame({"id": [1, 2, 3], "x": ["a", "b", "c"]})
>>> df2 = pd.DataFrame({"id": [2, 3, 3], "y": ["l", "m", "n"]})
```

```python
>>> df1 >> semi_join(_, df2)
   id  x
1   2  b
2   3  c
```

```python
>>> df1 >> anti_join(_, df2)
   id  x
0   1  a
```

Generally, it's a good idea to explicitly specify the on argument.

```python
>>> df1 >> anti_join(_, df2, on="id")
   id  x
0   1  a
```