"""Generate the submodules which import parts of griffe (e.g. dataclasses.py)

This process balances having to import specific objects from griffe, against
importing everything via the top-level griffe module. It does this by generating
modules for objects commonly used together in quartodoc.

* dataclasses: represent python objects
* docstrings: represent python docstrings
* expressions: represent annotation expressions

Run using: python -m quartodoc._griffe_compat._generate_stubs
"""

import ast
import black
import copy
import griffe
import inspect
from pathlib import Path


def fetch_submodule(ast_body, submodule: str):
    ast_imports = [
        obj
        for obj in ast_body
        if isinstance(obj, ast.ImportFrom) and obj.module == submodule
    ]

    if len(ast_imports) > 1:
        raise Exception(f"Found {len(ast_imports)} imports for {submodule}")
    elif not ast_imports:
        raise Exception(f"Could not find import for {submodule}")

    return ast_imports[0]


def code_for_imports(mod_code: str, submodules: list[str]) -> str:
    res = []
    mod = ast.parse(mod_code)
    for submod in submodules:
        expr = fetch_submodule(mod.body, submod)
        expr.module = "griffe"
        new_expr = copy.copy(expr)
        new_expr.module = "griffe"
        res.append(ast.unparse(new_expr))

    return black.format_str(
        "# flake8: noqa\n\n" + "\n".join(res), mode=black.FileMode()
    )


def generate_griffe_stub(out_path: Path, mod, submodules: list[str]):
    res = code_for_imports(inspect.getsource(mod), submodules)
    out_path.write_text(res)


MAPPINGS = {
    "dataclasses": [
        "_griffe.models",
        "_griffe.mixins",
        "_griffe.enumerations",
    ],
    "docstrings": ["_griffe.docstrings.models"],
    "expressions": ["_griffe.expressions"],
}

if __name__ == "__main__":
    for out_name, submodules in MAPPINGS.items():
        generate_griffe_stub(
            Path(__file__).parent / f"{out_name}.py", griffe, submodules
        )
