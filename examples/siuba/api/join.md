# join

`join(left, right, on=None, how=None, *args, by=None, **kwargs)`

Join two tables together, by matching on specified columns.

The functions inner_join, left_join, right_join, and full_join are provided
as wrappers around join, and are used in the examples.

## Parameters

| Name       | Type   | Description                                              | Default   |
|------------|--------|----------------------------------------------------------|-----------|
| `left`     |        | The left-hand table.                                     | required  |
| `right`    |        | The right-hand table.                                    | required  |
| `on`       |        | How to match them. Note that the keyword "by" can also be used for this
parameter, in order to support compatibility with dplyr.                                                          | `None`    |
| `how`      |        | The type of join to perform (inner, full, left, right).  | `None`    |
| `*args`    |        | Additional postition arguments. Currently not supported. | `()`      |
| `**kwargs` |        | Additional keyword arguments. Currently not supported.   | `{}`      |

## Returns

| Type         | Description   |
|--------------|---------------|
| pd.DataFrame |               |

## Examples

```python
>>> from siuba import _, inner_join, left_join, full_join, right_join
>>> from siuba.data import band_members, band_instruments, band_instruments2
>>> band_members
   name     band
0  Mick   Stones
1  John  Beatles
2  Paul  Beatles
```

```python
>>> band_instruments
    name   plays
0   John  guitar
1   Paul    bass
2  Keith  guitar
```

Notice that above, only John and Paul have entries for band instruments.
This means that they will be the only two rows in the inner_join result:

```python
>>> band_members >> inner_join(_, band_instruments)
   name     band   plays
0  John  Beatles  guitar
1  Paul  Beatles    bass
```

A left join ensures all original rows of the left hand data are included.

```python
>>> band_members >> left_join(_, band_instruments)
   name     band   plays
0  Mick   Stones     NaN
1  John  Beatles  guitar
2  Paul  Beatles    bass
```

A full join is similar, but ensures all rows of both data are included.

```python
>>> band_members >> full_join(_, band_instruments)
    name     band   plays
0   Mick   Stones     NaN
1   John  Beatles  guitar
2   Paul  Beatles    bass
3  Keith      NaN  guitar
```

You can explicilty specify columns to join on using the "by" argument:

```python
>>> band_members >> inner_join(_, band_instruments, by = "name")
   n...
```

Use a dictionary for the by argument, to match up columns with different names:

```python
>>> band_members >> full_join(_, band_instruments2, {"name": "artist"})
   n...
```

Joins create a new row for each pair of matches. For example, the value 1
is in two rows on the left, and 2 rows on the right so 4 rows will be created.

```python
>>> df1 = pd.DataFrame({"x": [1, 1, 3]})
>>> df2 = pd.DataFrame({"x": [1, 1, 2], "y": ["first", "second", "third"]})
>>> df1 >> left_join(_, df2)
   x       y
0  1   first
1  1  second
2  1   first
3  1  second
4  3     NaN
```

Missing values count as matches to eachother by default:

```python
>>> df3 = pd.DataFrame({"x": [1, None], "y": 2})
>>> df4 = pd.DataFrame({"x": [1, None], "z": 3})
>>> left_join(df3, df4)
     x  y  z
0  1.0  2  3
1  NaN  2  3
```