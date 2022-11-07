# select

`select(__data, *args, **kwargs)`

Select columns of a table to keep or drop (and optionally rename).

## Parameters

| Name       | Type   | Description                                       | Default   |
|------------|--------|---------------------------------------------------|-----------|
| `__data`   |        | The input table.                                  | required  |
| `*args`    |        | An expression specifying columns to keep or drop. | `()`      |
| `**kwargs` |        | Not implemented.                                  | `{}`      |

## Examples

```python
>>> from siuba import _, select
>>> from siuba.data import cars
```

```python
>>> small_cars = cars.head(1)
>>> small_cars
   cyl   mpg   hp
0    6  21.0  110
```

You can refer to columns by name or position.

```python
>>> small_cars >> select(_.cyl, _[2])
   cyl   hp
0    6  110
```

Use a `~` sign to exclude a column.

```python
>>> small_cars >> select(~_.cyl)
    mpg   hp
0  21.0  110
```

You can use any methods you'd find on the .columns.str accessor:

```python
>>> small_cars.columns.str.contains("p")
array([False,  True,  True])
```

```python
>>> small_cars >> select(_.contains("p"))
    mpg   hp
0  21.0  110
```

Use a slice to select a range of columns:

```python
>>> small_cars >> select(_[0:2])
   cyl   mpg
0    6  21.0
```

Multiple expressions can be combined using _[a, b, c] syntax. This is useful
for dropping a complex set of matches.

```python
>>> small_cars >> select(~_[_.startswith("c"), -1])
    mpg
0  21.0
```