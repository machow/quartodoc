# mutate

`mutate(__data, *args, **kwargs)`

Assign new variables to a DataFrame, while keeping existing ones.

## Parameters

| Name       | Type   | Description   | Default   |
|------------|--------|---------------|-----------|
| `__data`   |        |               | required  |
| `**kwargs` |        | new_col_name=value pairs, where value can be a function taking a singledispatch2
argument for the data being operated on.               | `{}`      |

See Also
--------
transmute : Returns a DataFrame with only the newly created columns.

## Examples

```python
>>> from siuba import _, mutate, head
>>> from siuba.data import cars
>>> cars >> mutate(cyl2 = _.cyl * 2, cyl4 = _.cyl2 * 2) >> head(2)
   cyl   mpg   hp  cyl2  cyl4
0    6  21.0  110    12    24
1    6  21.0  110    12    24
```