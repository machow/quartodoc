import sys

from pathlib import Path
from quartodoc import get_function, MdRenderer

# this could also be collected using static analysis
from siuba import __all__

root = Path(sys.argv[0]).parent

renderer = MdRenderer(header_level=1)

p = root / "api"
p.mkdir(exist_ok=True)

for name in __all__:
    if name in {
        # classes (https://github.com/machow/quartodoc/issues/2)
        "_",
        "Fx",
        # need resolve above issue, and a docstring hook
        # https://github.com/machow/quartodoc/issues/3
        "inner_join",
        "left_join",
        "full_join",
        "right_join",
    }:
        continue

    print(name)
    f_obj = get_function("siuba", name)
    p_func = p / f"{name}.md"
    p_func.write_text(renderer.to_md(f_obj))
