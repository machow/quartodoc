# count

`count(__data, *args, wt=None, sort=False, name=None, **kwargs)`

Summarize data with the number of rows for each grouping of data.

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
>>> from siuba import _, count, group_by, summarize, arrange
>>> from siuba.data import mtcars
```

```python
>>> count(mtcars, _.cyl, high_mpg = _.mpg > 30)
   cyl  high_mpg   n
0    4     False   7
1    4      True   4
2    6     False   7
3    8     False  14
```

Use sort to order results by number of observations (in descending order).

```python
>>> count(mtcars, _.cyl, sort=True)
   cyl   n
0    8  14
1    4  11
2    6   7
```

count is equivalent to doing a grouped summarize:

```python
>>> mtcars >> group_by(_.cyl) >> summarize(n = _.shape[0]) >> arrange(-_.n)
   cyl   n
2    8  14
0    4  11
1    6   7
```