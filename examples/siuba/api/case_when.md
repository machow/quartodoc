# case_when

`case_when(__data, cases: dict)`

Generalized, vectorized if statement.

## Parameters

| Name     | Type   | Description                     | Default   |
|----------|--------|---------------------------------|-----------|
| `__data` |        | The input data.                 | required  |
| `cases`  | dict   | A mapping of condition : value. | required  |

See Also
--------
if_else : Handles the special case of two conditions.
    

## Examples

```python
>>> import pandas as pd
>>> from siuba import _, case_when
```

```python
>>> df = pd.DataFrame({"x": [1, 2, 3]})
>>> case_when(df, {_.x == 1: "one", _.x == 2: "two"})
0     one
1     two
2    None
dtype: object
```

```python
>>> df >> case_when({_.x == 1: "one", _.x == 2: "two"})
0     one
1     two
2    None
dtype: object
```

```python
>>> df >> case_when({_.x == 1: "one", _.x == 2: "two", True: "other"})
0      one
1      two
2    other
dtype: object
```