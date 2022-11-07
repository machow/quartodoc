# head

`head(__data, n=5)`

Return the first n rows of the data.

## Parameters

| Name     | Type   | Description                         | Default   |
|----------|--------|-------------------------------------|-----------|
| `__data` |        | a DataFrame.                        | required  |
| `n`      |        | The number of rows of data to keep. | `5`       |

## Examples

```python
>>> from siuba import head
>>> from siuba.data import cars
```

```python
>>> cars >> head(2)
   cyl   mpg   hp
0    6  21.0  110
1    6  21.0  110
```