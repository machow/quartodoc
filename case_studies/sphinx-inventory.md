
# Sphinx inventory files

## Resources

- [sphinx inventory v2 field
  descriptions](https://sphobjinv.readthedocs.io/en/latest/syntax.html)

## Previewing an inventory file

``` bash
python -m sphinx.ext.intersphinx <file_name>
```

- [sphinx.util.inventory.InventoryFile](https://github.com/sphinx-doc/sphinx/blob/5e9550c78e3421dd7dcab037021d996841178f67/sphinx/util/inventory.py#L74)
  for opening the files.

``` python
from sphinx.util.inventory import InventoryFile
from os import path

SQLALCHEMY_DOCS_URL = "https://docs.sqlalchemy.org/"
SQLALCHEMY_INV_URL = f"{SQLALCHEMY_DOCS_URL}/objects.inv"

with open("objects_sqla.inv", "rb") as f:
    inv = InventoryFile.load(f, SQLALCHEMY_DOCS_URL, path.join)
```

``` python
list(inv)
```

    ['py:module',
     'py:function',
     'py:parameter',
     'py:class',
     'py:method',
     'py:attribute',
     'py:exception',
     'py:data',
     'std:label',
     'std:term',
     'std:doc']

``` python
inv["py:function"]["sqlalchemy.create_engine"]
```

    ('SQLAlchemy',
     '1.4',
     'https://docs.sqlalchemy.org/core/engines.html#sqlalchemy.create_engine',
     '-')
