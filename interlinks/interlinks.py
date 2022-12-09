import json
import panflute as pf

from plum import dispatch


inventory = {}


def ref_to_anchor(ref, text):
    # TODO: for now we just mutate el
    is_shortened = ref.startswith("~")

    stripped = ref.lstrip("~")

    try:
        entry = inventory[stripped]
        dst_url = entry["full_uri"]
    except KeyError:
        raise KeyError(f"Cross reference not found in an inventory file: {stripped}")

    if not text:
        if is_shortened:
            # shorten names from module.sub_module.func_name -> func_name
            name = pf.Str(entry["name"].split(".")[-1])
        else:
            name = pf.Str(entry["name"])
    else:
        # when the element is an Link, content is a ListContainer, but it has to be
        # *splatted back into Link?
        return pf.Link(*text, url=dst_url)

    return pf.Link(name, url=dst_url)


@dispatch
def visit(el, doc):
    return el
    # raise TypeError(f"Unsupported type: {type(el)}")


@dispatch
def visit(el: pf.MetaList, doc):
    meta = doc.get_metadata()

    for doc_name, cfg in meta["interlinks"]["sources"].items():
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
def visit(el: pf.Code, doc):
    # TODO: also need to remove ref. Should handle in parent?
    left_el = el.prev

    if left_el == pf.Str(":ref:"):
        return ref_to_anchor(el.text, None)

    return el


@dispatch
def visit(el: pf.Link, doc):
    if el.url.startswith("%60") and el.url.endswith("%60"):
        pf.debug("In a markdown link ref")

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
