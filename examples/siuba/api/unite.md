# unite

`unite(__data, col, *args, sep='_', remove=True)`

Combine multiple columns into a single column. Return DataFrame that column included.

## Parameters

| Name     | Type   | Description                                                         | Default   |
|----------|--------|---------------------------------------------------------------------|-----------|
| `__data` |        | a DataFrame                                                         | required  |
| `col`    |        | name of the to-be-created column (string).                          | required  |
| `*args`  |        | names of each column to combine.                                    | `()`      |
| `sep`    |        | separator joining each column being combined.                       | `'_'`     |
| `remove` |        | whether to remove the combined columns from the returned DataFrame. | `True`    |