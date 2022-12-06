import sys

from pathlib import Path
from quartodoc import get_object, MdRenderer, create_inventory, convert_inventory

# this could also be collected using static analysis
from siuba import __all__

BAD_FUNCS = {
    # classes (https://github.com/machow/quartodoc/issues/2)
    "_",
    "Fx",
    # need resolve above issue, and a docstring hook
    # https://github.com/machow/quartodoc/issues/3
    "inner_join",
    "left_join",
    "full_join",
    "right_join",
}

# +
root = Path(sys.argv[0]).parent
renderer = MdRenderer(header_level=1)

p = root / "api"
p.mkdir(exist_ok=True)
# -

# Stage 1: inventory file ----
all_objects = []
for name in __all__:
    if name in BAD_FUNCS:
        continue

    all_objects.append(get_object("siuba", name))

inv = create_inventory("siuba", "9.99", all_objects, uri=lambda s: f"api/{s.name}.html")
convert_inventory(inv, "objects.json")

# Stage 2: render api pages ----
for f_obj in all_objects:
    print(f_obj.name)
    p_func = p / f"{name}.md"
    p_func.write_text(renderer.to_md(f_obj))
