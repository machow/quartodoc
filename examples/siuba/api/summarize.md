# summarize

`summarize(__data, *args, **kwargs)`

Assign variables that are single number summaries of a DataFrame.

Grouped DataFrames will produce one row for each group. Otherwise, summarize
produces a DataFrame with a single row.

## Parameters

| Name       | Type   | Description                | Default   |
|------------|--------|----------------------------|-----------|
| `__data`   |        | The data being summarized. | required  |
| `**kwargs` |        | new_col_name=value pairs, where value can be a function taking
a single argument for the data being operated on.                            | `{}`      |

## Examples

```python
>>> from siuba import _, group_by, summarize
>>> from siuba.data import cars
```

```python
>>> cars >> summarize(avg = _.mpg.mean(), n = _.shape[0])
         avg   n
0  20.090625  32
```

```python
>>> g_cyl = cars >> group_by(_.cyl)
>>> g_cyl >> summarize(min = _.mpg.min())
   cyl   min
0    4  21.4
1    6  17.8
2    8  10.4
```

```python
>>> g_cyl >> summarize(mpg_std_err = _.mpg.std() / _.shape[0]**.5)
   cyl  mpg_std_err
0    4     1.359764
1    6     0.549397
2    8     0.684202
```