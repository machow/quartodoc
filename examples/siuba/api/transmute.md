# transmute

`transmute(__data, *args, **kwargs)`

Assign new columns to a DataFrame, while dropping previous columns.

## Parameters

| Name       | Type   | Description                                                           | Default   |
|------------|--------|-----------------------------------------------------------------------|-----------|
| `__data`   |        | The input data.                                                       | required  |
| `**kwargs` |        | Each keyword argument is the name of a new column, and an expression. | `{}`      |

See Also
--------
mutate : Assign new columns, or modify existing ones.

## Examples

```python
>>> from siuba import _, transmute, mutate, head
>>> from siuba.data import cars
```

Notice that transmute results in a table with only the new column:

```python
>>> cars >> transmute(cyl2 = _.cyl + 1) >> head(2)
   cyl2
0     7
1     7
```

By contrast, mutate adds the new column to the end of the table:

```python
>>> cars >>  mutate(cyl2 = _.cyl + 1) >> head(2)
   cyl   mpg   hp  cyl2
0    6  21.0  110     7
1    6  21.0  110     7
```