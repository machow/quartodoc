# tbl

`tbl(src, *args, **kwargs)`

Create a table from a data source.

## Parameters

| Name       | Type   | Description                                                        | Default   |
|------------|--------|--------------------------------------------------------------------|-----------|
| `src`      |        | A pandas DataFrame, SQLAlchemy Engine, or other registered object. | required  |
| `*args`    |        | Additional arguments passed to the individual implementations.     | `()`      |
| `**kwargs` |        | Additional arguments passed to the individual implementations.     | `()`      |

## Examples

```python
>>> from siuba.data import cars
```

A pandas DataFrame is already a table of data, so trivially returns itself.

```python
>>> tbl(cars) is cars
True
```

tbl() is useful for quickly connecting to a SQL database table.

```python
>>> from sqlalchemy import create_engine
>>> from siuba import count, show_query, collect
```

```python
>>> engine = create_engine("sqlite:///:memory:")
>>> cars.to_sql("cars", engine, index=False)
```

```python
>>> tbl_sql_cars = tbl(engine, "cars")
>>> tbl_sql_cars >> count()
# Source: lazy query
# DB Conn: Engine(sqlite:///:memory:)
# Preview:
    n
0  32
# .. may have more rows
```

When using duckdb, pass a DataFrame as the third argument to operate directly on it:

```python
>>> engine2 = create_engine("duckdb:///:memory:")
>>> tbl_cars_duck = tbl(engine, "cars", cars.head(2)) 
>>> tbl_cars_duck >> count() >> collect()
    n
0  32
```

You can analyze a mock table

```python
>>> from sqlalchemy import create_mock_engine
>>> from siuba import _
```

```python
>>> mock_engine = create_mock_engine("postgresql:///", lambda *args, **kwargs: None)
>>> tbl_mock = tbl(mock_engine, "some_table", columns = ["a", "b", "c"])
```

```python
>>> q = tbl_mock >> count(_.a) >> show_query()
SELECT some_table_1.a, count(*) AS n
FROM some_table AS some_table_1 GROUP BY some_table_1.a ORDER BY n DESC
```