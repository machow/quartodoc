import contextlib
import sphobjinv
import pytest
import yaml

from quartodoc import interlinks
from quartodoc.interlinks import (
    Inventories,
    Ref,
    TestSpec,
    TestSpecEntry,
    parse_md_style_link,
    Link,
    inventory_from_url,
)
from importlib_resources import files

# load test spec at import time, so that we can feed each spec entry
# as an individual test case using parametrize
_raw = yaml.safe_load(open(files("quartodoc") / "tests/example_interlinks/spec.yml"))
spec = TestSpec(__root__=_raw).__root__


@pytest.fixture
def invs():
    invs = Inventories.from_quarto_config(
        str(files("quartodoc") / "tests/example_interlinks/_quarto.yml")
    )

    return invs


# def test_inventories_from_config():
#     invs = Inventories.from_quarto_config(
#         str(files("quartodoc") / "tests/example_interlinks/_quarto.yml")
#     )


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


@pytest.mark.parametrize("entry", spec)
def test_spec_entry(invs: Inventories, entry: TestSpecEntry):
    ref_str, text = parse_md_style_link(entry.input)
    ref_str = ref_str.replace("`", "%60")  # weird, but matches pandoc

    # set up error and warning contexts ----
    # pytest uses context managers to check warnings and errors
    # so we either create the relevant cm or uses a no-op cm
    if entry.error:
        ctx_err = pytest.raises(getattr(interlinks, entry.error))
    else:
        ctx_err = contextlib.nullcontext()

    if entry.warning:
        ctx_warn = pytest.warns(UserWarning, match=entry.warning)
    else:
        ctx_warn = contextlib.nullcontext()

    # fetch link ----
    with ctx_warn as rec_warn, ctx_err as rec_err:  # noqa
        el = invs.pandoc_ref_to_anchor(ref_str, text)

    if entry.error:
        # return on errors, since no result produced
        return

    # output assertions ----
    if entry.output_link is not None or entry.output_text is not None:
        assert isinstance(el, Link)

        if entry.output_link:
            assert entry.output_link == el.url

        if entry.output_text:
            assert entry.output_text == el.content
    elif entry.output_element:
        assert el == entry.output_element


def test_inventory_from_url_local_roundtrip(tmp_path):
    inv = sphobjinv.Inventory()
    inv.project = "abc"
    inv.version = "0.0.1"

    soi_items = [
        sphobjinv.DataObjStr(
            name="foo", domain="py", role="method", priority="1", uri="$", dispname="-"
        )
    ]
    inv.objects.extend(soi_items)

    text = inv.data_file()
    sphobjinv.writebytes(tmp_path / "objects.txt", text)
    sphobjinv.writebytes(tmp_path / "objects.inv", sphobjinv.compress(text))

    res1 = inventory_from_url("file://" + str(tmp_path / "objects.txt"))
    res2 = inventory_from_url("file://" + str(tmp_path / "objects.inv"))

    assert isinstance(res1, sphobjinv.Inventory)
    assert isinstance(res2, sphobjinv.Inventory)
