# extract

`extract(__data, col, into, regex='(\\w+)', remove=True, convert=False, flags=0)`

Pull out len(into) fields from character strings. 

Returns a DataFrame with a column added for each piece.

## Parameters

| Name      | Type   | Description                                                                 | Default    |
|-----------|--------|-----------------------------------------------------------------------------|------------|
| `__data`  |        | a DataFrame                                                                 | required   |
| `col`     |        | name of column to split (either string, or siu expression).                 | required   |
| `into`    |        | names of resulting columns holding each entry in pulled out fields.         | required   |
| `regex`   |        | regular expression used to extract field. Passed to col.str.extract method. | `'(\\w+)'` |
| `remove`  |        | whether to remove col from the returned DataFrame.                          | `True`     |
| `convert` |        | whether to attempt to convert the split columns to numerics.                | `False`    |
| `flags`   |        | flags from the re module, passed to col.str.extract.                        | `0`        |