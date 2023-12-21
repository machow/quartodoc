import pytest

from quartodoc.pandoc.inlines import (
    Code,
    Emph,
    Image,
    Inline,
    Inlines,
    Link,
    Span,
    Str,
    Strong,
)
from quartodoc.pandoc.components import Attr

# NOTE:
# To make it easy to cross-check what the generated html code will be,
# it should be possible to copy the markdown code on the right-hand side
# of the assert statements and paste it at
# https://pandoc.org/try/


def test_code():
    s = "a = 1"

    c = Code(s)
    assert str(c) == "`a = 1`"
    assert c.html == "<code>a = 1</code>"

    c = Code(s, Attr("code-id", ["c1", "c2"]))
    assert str(c) == "`a = 1`{#code-id .c1 .c2}"
    assert c.html == '<code id="code-id" class="c1 c2">a = 1</code>'


def test_emph():
    e = Emph("a")
    assert str(e) == "*a*"

    e = Emph("")
    assert str(e) == ""


def test_image():
    img = Image("Image Caption", "path/to/image.png", "Image Title")
    assert str(img) == '![Image Caption](path/to/image.png "Image Title")'

    img = Image(
        src="image.png",
        attr=Attr(classes=["c1"], attributes={"width": "50%", "height": "60%"}),
    )
    assert str(img) == '![](image.png){.c1 width="50%" height="60%"}'


def test_inline():
    i = Inline()

    with pytest.raises(NotImplementedError):
        str(i)

    with pytest.raises(NotImplementedError):
        i.html


def test_inlines():
    i = Inlines(["a", Span("b"), Emph("c")])
    assert str(i) == "a [b]{} *c*"

    i = Inlines(["a", None, Span("b"), Emph("c"), None])
    assert str(i) == "a [b]{} *c*"

    i = Inlines([None, None, None])
    assert str(i) == ""

    i = Inlines(["a", Span("b"), Emph("c"), ["d", Strong("e")]])
    assert str(i) == "a [b]{} *c* d **e**"

    i = Inlines(["a", Span("b"), Emph("c"), Inlines(["d", Strong("e")])])
    assert str(i) == "a [b]{} *c* d **e**"


def test_link():
    l = Link("Link Text", "https://abc.com")
    assert str(l) == "[Link Text](https://abc.com)"

    l = Link("Link Text", "https://abc.com", "Link Title")
    assert str(l) == '[Link Text](https://abc.com "Link Title")'


def test_span():
    s = Span("a")
    assert str(s) == "[a]{}"

    s = Span("a", Attr("span-id", classes=["c1", "c2"], attributes={"data-value": "1"}))
    assert str(s) == '[a]{#span-id .c1 .c2 data-value="1"}'

    s = Span([Span("a"), Span("b"), "c"])
    assert str(s) == "[[a]{} [b]{} c]{}"


def test_str():
    s = Str("a")
    assert str(s) == "a"

    s = Str()
    assert str(s) == ""


def test_strong():
    s = Strong("a")
    assert str(s) == "**a**"

    s = Strong("")
    assert str(s) == ""


def test_seq_inlinecontent():
    s = Span(
        [Str("a"), Emph("b"), Code("c = 3", Attr(classes=["py"]))],
        Attr(classes=["c1", "c2"]),
    )
    assert str(s) == "[a *b* `c = 3`{.py}]{.c1 .c2}"
