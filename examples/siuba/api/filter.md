# filter

`filter(__data, *args)`

Keep rows where conditions are true.

## Parameters

| Name     | Type   | Description                                   | Default   |
|----------|--------|-----------------------------------------------|-----------|
| `__data` |        | The data being filtered.                      | required  |
| `*args`  |        | conditions that must be met to keep a column. | `()`      |

## Examples

```python
>>> from siuba import _, filter
>>> from siuba.data import cars
```

Keep rows where cyl is 4 *and* mpg is less than 25.

```python
>>> cars >> filter(_.cyl ==  4, _.mpg < 22) 
    cyl   mpg   hp
20    4  21.5   97
31    4  21.4  109
```

Use `|` to represent an OR condition. For example, the code below keeps
rows where hp is over 250 *or* mpg is over 32.

```python
>>> cars >> filter((_.hp > 300) | (_.mpg > 32))
    cyl   mpg   hp
17    4  32.4   66
19    4  33.9   65
30    8  15.0  335
```