from quartodoc.pandoc.blocks import Blocks, Div
from quartodoc.pandoc.meta import Meta

# NOTE:
# To make it easy to cross-check what the generated html code will be,
# it should be possible to copy the markdown code on the right-hand side
# of the assert statements and paste it at
# https://pandoc.org/try/


def test_meta():
    meta = Meta({
        "token": "value",
        "integer": 42,
        "float": 3.14157,
        "boolean": True,
        "none": None,
        "sentence": "This is a sentence that ends with a colon :",
        "list-of-values": ["first", "second", "third"],
        "nest": {
            "name": "joe",
            "hobbies": ["gaming", "hiking"],
            "parents": {
                "father": "Joe's Father",
                "mother": "Joe's Mother",
            }
        }
    })
    b = Blocks([meta, Div("a")])

    assert (str(b) == """
---
token: value
integer: 42
float: 3.14157
boolean: true
none: null
sentence: 'This is a sentence that ends with a colon :'
list-of-values:
- first
- second
- third
nest:
  name: joe
  hobbies:
  - gaming
  - hiking
  parents:
    father: Joe's Father
    mother: Joe's Mother
---

::: {}
a
:::
""".strip()
)
