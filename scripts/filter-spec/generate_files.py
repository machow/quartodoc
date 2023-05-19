# %%
from quartodoc import blueprint, collect, create_inventory, convert_inventory
import quartodoc.layout as lo
import shutil

from pathlib import Path

repo_dir = Path(__file__).parent.parent.parent
base_dir = repo_dir / "quartodoc" / "tests" / "example_interlinks"
base_dir.mkdir(exist_ok=True, parents=True)

shutil.copy(Path(__file__).parent / "_quarto.yml", base_dir / "_quarto.yml")


# %%
layout = lo.Layout(
    sections=[
        lo.Section(
            title="some title",
            desc="some description",
            contents=[
                lo.Auto(name="layout", members=[]),
                lo.Auto(name="MdRenderer", members=["style", "render"]),
            ],
        )
    ],
    package="quartodoc",
)

bp = blueprint(layout)
pages, items = collect(bp, "api")
inv = create_inventory("quartodoc", "0.0.999", items)
convert_inventory(inv, base_dir / "objects.json")

# %%
layout2 = lo.Layout(
    sections=[
        lo.Section(
            title="some title",
            desc="some description",
            contents=[lo.Auto(name="get_object")],
        )
    ],
    package="quartodoc",
)

_, items2 = collect(blueprint(layout2), "api")
inv2 = create_inventory("other", "0.0.999", items2)

p_inv = base_dir / "_inv"
p_inv.mkdir(exist_ok=True)

convert_inventory(inv2, p_inv / "other_objects.json")
# %%
