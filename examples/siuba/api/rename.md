# rename

`rename(__data, **kwargs)`

Rename columns of a table.

## Parameters

| Name       | Type   | Description                                                                    | Default   |
|------------|--------|--------------------------------------------------------------------------------|-----------|
| `__data`   |        | The input table.                                                               | required  |
| `**kwargs` |        | Keyword arguments of the form new_name = _.old_name, or new_name = "old_name". | `{}`      |

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, rename, select
```

```python
>>> df = pd.DataFrame({"zzz": [1], "b": [2]})
>>> df >> rename(a = _.zzz)
   a  b
0  1  2
```

Note that this is equivalent to this select code:

```python
>>> df >> select(_.a == _.zzz, _.b)
   a  b
0  1  2
```