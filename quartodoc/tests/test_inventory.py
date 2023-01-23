import pytest

from quartodoc.inventory import Ref


@pytest.mark.parametrize(
    "raw,dst",
    [
        ("`print`", Ref(target="print")),
        (":function:`print`", Ref(role="function", target="print")),
        (":py:function:`print`", Ref(domain="py", role="function", target="print")),
        (
            ":external:function:`print`",
            Ref(role="function", target="print", external=True),
        ),
        (":external+abc:`print`", Ref(target="print", invname="abc", external=True)),
    ],
)
def test_ref_from_string(raw, dst):
    src = Ref.from_string(raw)

    assert src == dst
