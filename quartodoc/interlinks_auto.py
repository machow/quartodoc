from __future__ import annotations

import jedi

import ast
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from typing_extensions import TypeAlias, Union

ASTItems: TypeAlias = Union[ast.Call, ast.Name, ast.Attribute]


class CallVisitor(ast.NodeVisitor):
    results: list[ASTItems]

    def __init__(self):
        self.results = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.results.append(node)
            return self.visit(node.func.value)
        elif isinstance(node.func, ast.Name):
            self.results.append(node)

    def visit_Name(self, node):
        self.results.append(node)

    def visit_Attribute(self, node):
        self.results.append(node)

    def reset(self):
        self.results = []

        return self

    @classmethod
    def analyze(cls, code) -> list[Interlink]:
        visitor = cls()
        visitor.visit(ast.parse(code))
        script = jedi.Script(code)
        all_links = [node_to_interlink_name(script, call) for call in visitor.results]
        return [link for link in all_links if link is not None]


def narrow_node_start(node: ast.AST) -> tuple[int, int]:
    if isinstance(node, ast.Attribute):
        return (node.value.end_lineno, node.value.end_col_offset)

    return node.lineno, node.col_offset


def node_to_interlink_name(script: jedi.Script, node: ast.AST) -> Interlink | None:
    print(node.func.lineno, node.func.end_col_offset)
    try:
        func = node.func
        name = script.goto(func.lineno, func.end_col_offset)[0]
        full_name = name.full_name
        lineno, col_offset = narrow_node_start(func)
        return Interlink(
            name=full_name,
            lineno=lineno,
            end_lineno=func.end_lineno,
            col_offset=col_offset,
            end_col_offset=func.end_col_offset,
        )
    except IndexError:
        return None


class Code(BaseModel):
    content: str


class Interlink(BaseModel):
    name: str
    lineno: int
    end_lineno: int
    col_offset: int
    end_col_offset: int


app = FastAPI()


@app.post("/analyze")
async def analyze(code: Code):
    res = CallVisitor.analyze(code.content)
    return {"interlinks": res}


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1])
    uvicorn.run(app, port=port, host="0.0.0.0")
