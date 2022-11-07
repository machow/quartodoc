# separate

`separate(__data, col, into, sep='[^a-zA-Z0-9]', remove=True, convert=False, extra='warn', fill='warn')`

Split col into len(into) piece. Return DataFrame with a column added for each piece.

## Parameters

| Name      | Type   | Description                                                              | Default          |
|-----------|--------|--------------------------------------------------------------------------|------------------|
| `__data`  |        | a DataFrame.                                                             | required         |
| `col`     |        | name of column to split (either string, or siu expression).              | required         |
| `into`    |        | names of resulting columns holding each entry in split.                  | required         |
| `sep`     |        | regular expression used to split col. Passed to col.str.split method.    | `'[^a-zA-Z0-9]'` |
| `remove`  |        | whether to remove col from the returned DataFrame.                       | `True`           |
| `convert` |        | whether to attempt to convert the split columns to numerics.             | `False`          |
| `extra`   |        | what to do when more splits than into names.  One of ("warn", "drop" or "merge").
"warn" produces a warning; "drop" and "merge" currently not implemented.                                                                          | `'warn'`         |
| `fill`    |        | what to do when fewer splits than into names. Currently not implemented. | `'warn'`         |

## Examples

```python
>>> import pandas as pd
>>> from siuba import separate
```

```python
>>> df = pd.DataFrame({"label": ["S1-1", "S2-2"]})
```

Split into two columns:

```python
>>> separate(df, "label", into = ["season", "episode"])
  season episode
0     S1       1
1     S2       2
```

Split, and try to convert columns to numerics:

```python
>>> separate(df, "label", into = ["season", "episode"], convert = True)
  season  episode
0     S1        1
1     S2        2
```