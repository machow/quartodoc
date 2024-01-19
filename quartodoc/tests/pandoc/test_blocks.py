import pytest

from quartodoc.pandoc.components import Attr
from quartodoc.pandoc.blocks import (
    Block,
    Blocks,
    BulletList,
    CodeBlock,
    DefinitionList,
    Div,
    Header,
    OrderedList,
    Para,
    Plain,
)
from quartodoc.pandoc.inlines import Span, Link

# NOTE:
# To make it easy to cross-check what the generated html code will be,
# it should be possible to copy the markdown code on the right-hand side
# of the assert statements and paste it at
# https://pandoc.org/try/


def test_block():
    b = Block()

    with pytest.raises(NotImplementedError):
        str(b)

    with pytest.raises(NotImplementedError):
        b.html


def test_blocks():
    b = Blocks(
        [
            Div("a", Attr("id-1", ["c1", "c2"])),
            CodeBlock("b = 2"),
            Div("c"),
            Blocks([Span("d"), Div("e")]),
        ]
    )
    assert (
        str(b)
        == """
::: {#id-1 .c1 .c2}
a
:::

```
b = 2
```

::: {}
c
:::

[d]{}

::: {}
e
:::
""".strip()
    )

    b = Blocks([Div("a"), Div("b"), [Div("c"), Div("d")]])
    assert (
        str(b)
        == """
::: {}
a
:::

::: {}
b
:::

::: {}
c
:::

::: {}
d
:::
""".strip()
    )

    b = Blocks([Div("a"), None, Div("c")])
    assert (
        str(b)
        == """
::: {}
a
:::

::: {}
c
:::
""".strip()
    )

    b1 = Blocks([None, None])
    b2 = Blocks(["", "", ""])
    assert str(b1) == ""
    assert str(b2) == ""


def test_bulletlist():
    b = BulletList(["a", "b", "c"])
    assert (
        str(b)
        == """
* a
* b
* c
""".strip()
    )

    b = BulletList([Para("a"), Para("b"), Para("c")])
    assert (
        str(b)
        == """
* a

* b

* c
""".strip()
    )

    b = BulletList(["a", CodeBlock("b = 2"), "c", "d"])
    assert (
        str(b)
        == """
* a
*
  ```
  b = 2
  ```

* c
* d
""".strip()
    )

    b = BulletList([Para("a"), CodeBlock("b = 2"), Para("c"), Para("d")])
    assert (
        str(b)
        == """
* a

*
  ```
  b = 2
  ```

* c

* d
""".strip()
    )

    b = BulletList([BulletList(["a", "b", "c"]), BulletList(["d", "e", "f"])])
    assert (
        str(b)
        == """
* * a
  * b
  * c

* * d
  * e
  * f
""".strip()
    )


def test_codeblock():
    c = CodeBlock("a = 1")
    assert (
        str(c)
        == """
```
a = 1
```
""".strip()
    )

    c = CodeBlock("a = 1", Attr(classes=["py"]))
    assert (
        str(c)
        == """
```py
a = 1
```
""".strip()
    )

    c = CodeBlock("a = 1", Attr(classes=["py", "c1"]))
    assert (
        str(c)
        == """
``` {.py .c1}
a = 1
```
""".strip()
    )


def test_definitionlist():
    d = DefinitionList(
        [
            ("Term 1", "Definition 1"),
            ("Term 2", "Definition 2"),
        ]
    )
    assert (
        str(d)
        == """
Term 1

:   Definition 1

Term 2

:   Definition 2
""".strip()
    )

    d = DefinitionList(
        [
            ("Term 1", ("1st Definition of Term 1", "2nd Definition of Term 1")),
            ("Term 2", ("1st Definition of Term 2", "2nd Definition of Term 2")),
        ]
    )
    assert (
        str(d)
        == """
Term 1

:   1st Definition of Term 1

:   2nd Definition of Term 1

Term 2

:   1st Definition of Term 2

:   2nd Definition of Term 2
""".strip()
    )

    d = DefinitionList(
        [
            ([Span("Term 1 - Span 1"), Span("Term 1 - Span 2")], "Definition 1"),
            ([Span("Term 2 - Span 1"), Span("Term 2 - Span 2")], "Definition 2"),
        ]
    )
    assert (
        str(d)
        == """
[Term 1 - Span 1]{} [Term 1 - Span 2]{}

:   Definition 1

[Term 2 - Span 1]{} [Term 2 - Span 2]{}

:   Definition 2
""".strip()
    )

    d = DefinitionList(
        [
            ("Term 1", Blocks([Div("Definition of 1"), CodeBlock("var_1 = 1")])),
            ("Term 2", Blocks([Div("Definition of 2"), CodeBlock("var_2 = 2")])),
        ]
    )
    assert (
        str(d)
        == """
Term 1

:   ::: {}
    Definition of 1
    :::

    ```
    var_1 = 1
    ```

Term 2

:   ::: {}
    Definition of 2
    :::

    ```
    var_2 = 2
    ```
""".strip()
    )

    # Empty definitions are valid, but require trailling spaces after
    # the colon
    d1 = DefinitionList([("Term 1", ""), ("Term 2", "Definition 2")])
    d2 = DefinitionList([("Term 1", None), ("Term 2", "Definition 2")])
    assert ":   \n" in str(d1)
    assert str(d1) == str(d2)


def test_div():
    d = Div("a")
    assert (
        str(d)
        == """
::: {}
a
:::
""".strip()
    )

    d = Div("a", Attr("div-id", classes=["c1", "c2"]))
    assert (
        str(d)
        == """
::: {#div-id .c1 .c2}
a
:::
""".strip()
    )


def test_header():
    h = Header(1, "A")
    assert str(h) == "# A"

    h = Header(2, "A", Attr("header-id", classes=["c1", "c2"]))
    assert str(h) == "## A {#header-id .c1 .c2}"


def test_orderedlist():
    o = OrderedList(["a", "b", "c"])
    assert (
        str(o)
        == """
1. a
2. b
3. c
""".strip()
    )

    o = OrderedList([Para("a"), Para("b"), Para("c")])
    assert (
        str(o)
        == """
1. a

2. b

3. c
""".strip()
    )

    o = OrderedList(["a", CodeBlock("b = 2"), "c", "d"])
    assert (
        str(o)
        == """
1. a
2.
   ```
   b = 2
   ```

3. c
4. d
""".strip()
    )

    o = OrderedList([Para("a"), CodeBlock("b = 2"), Para("c"), Para("d")])
    assert (
        str(o)
        == """
1. a

2.
   ```
   b = 2
   ```

3. c

4. d
""".strip()
    )

    o = OrderedList([OrderedList(["a", "b", "c"]), OrderedList(["d", "e", "f"])])
    assert (
        str(o)
        == """
1. 1. a
   2. b
   3. c

2. 1. d
   2. e
   3. f
""".strip()
    )


def test_para():
    p = Para("A")
    assert (
        str(p)
        == """
A
"""
    )


def test_plain():
    p = Plain("A")
    assert str(p) == "A"
