# group_by

`group_by(__data, *args, add=False, **kwargs)`

Return a grouped DataFrame, using columns or expressions to define groups.

Any operations (e.g. summarize, mutate, filter) performed on grouped data
will be performed "by group". Use `ungroup()` to remove the groupings.

## Parameters

| Name       | Type   | Description                                                                     | Default   |
|------------|--------|---------------------------------------------------------------------------------|-----------|
| `__data`   |        | The data being grouped.                                                         | required  |
| `*args`    |        | Lazy expressions used to select the grouping columns. Currently, each
arg must refer to a single columns (e.g. _.cyl, _.mpg).                                                                                 | `()`      |
| `add`      |        | If the data is already grouped, whether to add these groupings on top of those. | `False`   |
| `**kwargs` |        | Keyword arguments define new columns used to group the data.                    | `{}`      |

## Examples

```python
>>> from siuba import _, group_by, summarize, filter, mutate, head
>>> from siuba.data import cars
```

```python
>>> by_cyl = cars >> group_by(_.cyl)
```

```python
>>> by_cyl >> summarize(max_mpg = _.mpg.max(), max_hp = _.hp.max())
   cyl  max_mpg  max_hp
0    4     33.9     113
1    6     21.4     175
2    8     19.2     335
```

```python
>>> by_cyl >> filter(_.mpg == _.mpg.max())
(grouped data frame)
    cyl   mpg   hp
3     6  21.4  110
19    4  33.9   65
24    8  19.2  175
```

```python
>>> cars >> group_by(cyl2 = _.cyl + 1) >> head(2)
(grouped data frame)
   cyl   mpg   hp  cyl2
0    6  21.0  110     7
1    6  21.0  110     7
```

Note that creating the new grouping column is always performed on ungrouped data.
Use an explicit mutate on the grouped data perform the operation within groups.

For example, the code below calls pd.cut on the mpg column, within each cyl group.

```python
>>> from siuba.siu import call
>>> (cars
...     >> group_by(_.cyl)
...     >> mutate(mpg_bin = call(pd.cut, _.mpg, 3))
...     >> group_by(_.mpg_bin, add=True)
...     >> head(2)
... )
(grouped data frame)
   cyl   mpg   hp       mpg_bin
0    6  21.0  110  (20.2, 21.4]
1    6  21.0  110  (20.2, 21.4]
```