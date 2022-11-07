# expand

`expand(__data, *args, fill=None)`

Return table with unique crossings of specified columns.

## Parameters

| Name     | Type   | Description                             | Default   |
|----------|--------|-----------------------------------------|-----------|
| `__data` |        | The input data.                         | required  |
| `*args`  |        | Column names to cross and de-duplicate. | `()`      |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, expand, count, anti_join, right_join
```

```python
>>> df = pd.DataFrame({"x": [1, 2, 2], "y": ["a", "a", "b"], "z": 1})
>>> df
   x  y  z
0  1  a  1
1  2  a  1
2  2  b  1
```

```python
>>> combos = df >> expand(_.x, _.y)
>>> combos
   x  y
0  1  a
1  1  b
2  2  a
3  2  b
```

```python
>>> df >> right_join(_, combos)
   x  y    z
0  1  a  1.0
1  1  b  NaN
2  2  a  1.0
3  2  b  1.0
```

```python
>>> combos >> anti_join(_, df)
   x  y
1  1  b
```

Note that expand will also cross missing values: 

```python
>>> df2 = pd.DataFrame({"x": [1, None], "y": [3, 4]})
>>> expand(df2, _.x, _.y)
     x  y
0  1.0  3
1  1.0  4
2  NaN  3
3  NaN  4
```

It will also cross all levels of a categorical (even those not in the data):

```python
>>> df3 = pd.DataFrame({"x": pd.Categorical(["a"], ["a", "b"])})
>>> expand(df3, _.x)
   x
0  a
1  b
```