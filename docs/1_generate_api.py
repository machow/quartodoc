import sys

from pathlib import Path
from quartodoc import (
    get_object,
    MdRenderer,
    create_inventory,
    convert_inventory,
    __version__,
)

FUNCTIONS = [
    "get_object",
    "create_inventory",
    "convert_inventory",
    "MdRenderer",
]

PACKAGE = "quartodoc"

# +
root = Path(sys.argv[0]).parent
renderer = MdRenderer(header_level=1)

p = root / "api"
p.mkdir(exist_ok=True)
# -

# Stage 1: inventory file ----
all_objects = []
for name in FUNCTIONS:
    all_objects.append(get_object(PACKAGE, name))

inv = create_inventory(
    PACKAGE,
    __version__,
    all_objects,
    uri=lambda s: f"api/#{s.name}",
    dispname=lambda s: f"{s.name}",
)
convert_inventory(inv, "objects.json")

# Stage 2: render api pages ----
all_content = []
for f_obj in all_objects:
    print(f_obj.name)
    content = renderer.to_md(f_obj)
    all_content.append(content)

    # p_func = p / f"{f_obj.name}.md"
    # p_func.write_text(content)

(p / "index.md").write_text("\n\n".join(all_content))
