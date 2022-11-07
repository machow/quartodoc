# ungroup

`ungroup(__data)`

Return an ungrouped DataFrame.

## Parameters

| Name     | Type   | Description               | Default   |
|----------|--------|---------------------------|-----------|
| `__data` |        | The data being ungrouped. | required  |

## Examples

```python
>>> from siuba import _, group_by, ungroup
>>> from siuba.data import cars
```

```python
>>> g_cyl = cars.groupby("cyl")
>>> res1 = ungroup(g_cyl)
```

```python
>>> res2 = cars >> group_by(_.cyl) >> ungroup()
```