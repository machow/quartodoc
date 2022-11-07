# add_count

`add_count(__data, *args, wt=None, sort=False, name=None, **kwargs)`

Add a column that is the number of observations for each grouping of data.

Note that this function is similar to count(), but does not aggregate. It's
useful combined with filter().

## Parameters

| Name       | Type   | Description                                                            | Default   |
|------------|--------|------------------------------------------------------------------------|-----------|
| `__data`   |        | A DataFrame.                                                           | required  |
| `*args`    |        | The names of columns to be used for grouping. Passed to group_by.      | `()`      |
| `wt`       |        | The name of a column to use as a weighted for each row.                | `None`    |
| `sort`     |        | Whether to sort the results in descending order.                       | `False`   |
| `**kwargs` |        | Creates a new named column, and uses for grouping. Passed to group_by. | `{}`      |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, add_count, group_by, ungroup, mutate
>>> from siuba.data import mtcars
```

```python
>>> df = pd.DataFrame({"x": ["a", "a", "b"], "y": [1, 2, 3]})
>>> df >> add_count(_.x)
   x  y  n
0  a  1  2
1  a  2  2
2  b  3  1
```

This is useful if you want to see data associated with some count:

```python
>>> df >> add_count(_.x) >> filter(_.n == 1)
   x  y  n
2  b  3  1
```

Note that add_count is equivalent to a grouped mutate:

```python
>>> df >> group_by(_.x) >> mutate(n = _.shape[0]) >> ungroup()
   x  y  n
0  a  1  2
1  a  2  2
2  b  3  1
```