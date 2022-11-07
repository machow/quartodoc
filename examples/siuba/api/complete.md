# complete

`complete(__data, *args, fill=None, explicit=True)`

Add rows to fill in missing combinations in the data.

This is a wrapper around expand(), right_join(), along with filling NAs.

## Parameters

| Name       | Type   | Description                  | Default   |
|------------|--------|------------------------------|-----------|
| `__data`   |        | The input data.              | required  |
| `*args`    |        | Columns to cross and expand. | `()`      |
| `fill`     |        | A dictionary specifying what to use for missing values in each column.
If a column is not specified, missing values are left as is.                              | `None`    |
| `explicit` |        | Should both NAs created by the complete and pre-existing NAs be filled
by the fill argument? Defaults to True (filling both). When set to False,
it will only fill newly created NAs.                              | `True`    |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, expand, count, anti_join, right_join
```

```python
>>> df = pd.DataFrame({"x": [1, 2, 2], "y": ["a", "a", "b"], "z": [8, 9, None]})
>>> df
   x  y    z
0  1  a  8.0
1  2  a  9.0
2  2  b  NaN
```

```python
>>> df >> complete(_.x, _.y)
   x  y    z
0  1  a  8.0
1  1  b  NaN
2  2  a  9.0
3  2  b  NaN
```

Use the fill argument to replace missing values:

```python
>>> df >> complete(_.x, _.y, fill={"z": 999})
   x  y      z
0  1  a    8.0
1  1  b  999.0
2  2  a    9.0
3  2  b  999.0
```

A common use of complete is to make zero counts explicit (e.g. for charting):

```python
>>> df >> count(_.x, _.y) >> complete(_.x, _.y, fill={"n": 0})
   x  y    n
0  1  a  1.0
1  1  b  0.0
2  2  a  1.0
3  2  b  1.0
```

Use explicit=False to only fill the NaNs introduced by complete (implicit missing),
and not those already in the original data (explicit missing):

```python
>>> df >> complete(_.x, _.y, fill={"z": 999}, explicit=False)
   x  y      z
0  1  a    8.0
1  1  b  999.0
2  2  a    9.0
3  2  b    NaN
```