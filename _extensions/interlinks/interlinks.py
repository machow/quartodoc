import json
import panflute as pf

from plum import dispatch


inventory = {}


class ConfigError(Exception):
    pass


def load_mock_inventory(items: "dict[str, str]"):
    for k, v in items.items():
        inventory[k] = v


def ref_to_anchor(ref: str, text: "str | pf.ListContainer | None"):
    """Return a Link element based on ref in interlink format

    Parameters
    ----------
    ref:
        The interlink reference (e.g. "my_module.my_function").
    text:
        The text to be displayed for the link.

    Examples
    --------

    >>> url = "https://example.org/functools.partial.html"
    >>> load_mock_inventory({"functools.partial": {"full_uri": url, "name": "functools.partial"}})
    >>> ref_to_anchor("functools.partial")
    Link(Str(functools.partial); url='https://example.org/functools.partial.html')

    >>> ref_to_anchor("~functools.partial")
    Link(Str(partial); url='https://example.org/functools.partial.html')
    """
    # TODO: for now we just mutate el
    is_shortened = ref.startswith("~")

    stripped = ref.lstrip("~")

    try:
        entry = inventory[stripped]
        dst_url = entry["full_uri"]
    except KeyError:
        raise KeyError(f"Cross reference not found in an inventory file: {stripped}")

    pf.debug(f"TEXT IS: {text}")
    if not text:
        name = entry["name"] if entry["dispname"] == "-" else entry["dispname"]
        if is_shortened:
            # shorten names from module.sub_module.func_name -> func_name
            name = pf.Str(name.split(".")[-1])
        else:
            name = pf.Str(name)
    else:
        # when the element is an Link, content is a ListContainer, but it has to be
        # *splatted back into Link?
        if isinstance(text, pf.ListContainer):
            return pf.Link(*text, url=dst_url)
        elif isinstance(text, str):
            return pf.Link(pf.Str(text), url=dst_url)
        else:
            raise TypeError(f"Unsupported type: {type(text)}")

    return pf.Link(name, url=dst_url)


def parse_rst_style_ref(full_text):
    """
    Returns
    -------
    tuple
        The parsed title (None if no title specified), and corresponding reference.
    """

    import re

    # pf.debug(full_text)

    m = re.match(r"(?P<text>.+?)\<(?P<ref>[a-zA-Z\.\-: _]+)\>", full_text)
    if m is None:
        # TODO: print a warning or something
        return full_text, None

    text, ref = m.groups()

    return ref, text


# Visitor ================================================================================


@dispatch
def visit(el, doc):
    return el
    # raise TypeError(f"Unsupported type: {type(el)}")


@dispatch
def visit(el: pf.MetaList, doc):
    meta = doc.get_metadata()

    try:
        sources = meta["interlinks"]["sources"]
    except KeyError:
        raise ConfigError(
            "No interlinks.sources field detected in your metadata."
            "Please add this to your header:\n\n"
            "interlinks:"
            "\n sources:"
            "\n    - <source_name>: {url: ..., inv: ..., fallback: ... }"
        )
    for doc_name, cfg in sources.items():
        json_data = json.load(open(cfg["fallback"]))

        for item in json_data["items"]:
            # TODO: what are the rules for inventories with overlapping names?
            #       it seems like this is where priority and using source name as an
            #       optional prefix in references is useful (e.g. siuba:a.b.c).
            full_uri = cfg["url"] + item["uri"].replace("$", item["name"])
            enh_item = {**item, "full_uri": full_uri}
            inventory[item["name"]] = enh_item

    return el


@dispatch
def visit(el: pf.Doc, doc):
    return el


@dispatch
def visit(el: pf.Plain, doc):
    cont = el.content
    if len(cont) == 2 and cont[0] == pf.Str(":ref:") and isinstance(cont[1], pf.Code):
        _, code = el.content

        ref, title = parse_rst_style_ref(code.text)

        return pf.Plain(ref_to_anchor(ref, title))

    return el


@dispatch
def visit(el: pf.Link, doc):
    if el.url.startswith("%60") and el.url.endswith("%60"):
        url = el.url[3:-3]

        # Get URL ----

        # TODO: url can be form external+invname:domain:reftype:target
        # for now, assume it's simply <target>. e.g. siuba.dply.verbs.mutate
        return ref_to_anchor(url, el.content)

    return el


def main(doc=None):
    return pf.run_filter(visit, doc=None)


if __name__ == "__main__":
    main()
