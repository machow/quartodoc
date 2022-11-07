# show_query

`show_query(__data, simplify=False)`

Print the details of a query.

## Parameters

| Name       | Type   | Description                                              | Default   |
|------------|--------|----------------------------------------------------------|-----------|
| `__data`   |        | A DataFrame of siuba.sql.LazyTbl.                        | required  |
| `simplify` |        | Whether to attempt to simplify the query.                | `False`   |
| `**kwargs` |        | Additional arguments passed to specific implementations. | required  |