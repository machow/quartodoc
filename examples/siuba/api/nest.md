# nest

`nest(__data, *args, key='data')`

Nest columns within a DataFrame.

## Parameters

| Name     | Type   | Description                                               | Default   |
|----------|--------|-----------------------------------------------------------|-----------|
| `__data` |        | A DataFrame.                                              | required  |
| `*args`  |        | The names of columns to be nested. May use any syntax used by the
`select` function.                                                           | `()`      |
| `key`    |        | The name of the column that will hold the nested columns. | `'data'`  |

## Examples

```python
>>> from siuba import _, nest
>>> from siuba.data import cars
>>> nested_cars = cars >> nest(-_.cyl)
```

Note that pandas with nested DataFrames looks okay in juypter notebooks,
but has a weird representation in the IPython console, so the example below
shows that each entry in the data column is a DataFrame.

```python
>>> nested_cars.shape
(3, 2)
```

```python
>>> type(nested_cars.data[0])
<class 'pandas.core.frame.DataFrame'>
```