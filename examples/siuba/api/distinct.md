# distinct

`distinct(__data, *args, _keep_all=False, **kwargs)`

Keep only distinct (unique) rows from a table.

## Parameters

| Name        | Type   | Description                                                       | Default   |
|-------------|--------|-------------------------------------------------------------------|-----------|
| `__data`    |        | The input data.                                                   | required  |
| `*args`     |        | Columns to use when determining which rows are unique.            | `()`      |
| `_keep_all` |        | Whether to keep all columns of the original data, not just *args. | `False`   |
| `**kwargs`  |        | If specified, arguments passed to the verb mutate(), and then being used
in distinct().                                                                   | `{}`      |

See Also
--------
count : keep distinct rows, and count their number of observations.

## Examples

```python
>>> from siuba import _, distinct, select
>>> from siuba.data import penguins
```

```python
>>> penguins >> distinct(_.species, _.island)
     species     island
0     Adelie  Torgersen
1     Adelie     Biscoe
2     Adelie      Dream
3     Gentoo     Biscoe
4  Chinstrap      Dream
```

Use _keep_all=True, to keep all columns in each distinct row. This lets you
peak at the values of the first unique row.

```python
>>> small_penguins = penguins >> select(_[:4])
>>> small_penguins >> distinct(_.species, _keep_all = True)
     species     island  bill_length_mm  bill_depth_mm
0     Adelie  Torgersen            39.1           18.7
1     Gentoo     Biscoe            46.1           13.2
2  Chinstrap      Dream            46.5           17.9
```