# if_else

`if_else(condition, true, false)`

## Parameters

| Name        | Type   | Description                                | Default   |
|-------------|--------|--------------------------------------------|-----------|
| `condition` |        | Logical vector (or lazy expression).       | required  |
| `true`      |        | Values to be used when condition is True.  | required  |
| `false`     |        | Values to be used when condition is False. | required  |

See Also
--------
case_when : Generalized if_else, for handling many cases.
    

## Examples

```python
>>> ser1 = pd.Series([1,2,3])
>>> if_else(ser1 > 2, np.nan, ser1)
0    1.0
1    2.0
2    NaN
dtype: float64
```

```python
>>> from siuba import _
>>> f = if_else(_ < 2, _, 2)
>>> f(ser1)
0    1
1    2
2    2
dtype: int64
```

```python
>>> import numpy as np
>>> ser2 = pd.Series(['NA', 'a', 'b'])
>>> if_else(ser2 == 'NA', np.nan, ser2)
0    NaN
1      a
2      b
dtype: object
```