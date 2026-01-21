from shiny.express import render, ui, input
from quartodoc.interlinks_auto import CallVisitor

ui.input_text_area("raw_code", "Code"),


@render.code
def code():
    res = CallVisitor().analyze(input.raw_code())
    chars = [list(row) for row in input.raw_code().split("\n")]
    print(chars)
    for inter in res:
        ii, jj = inter.lineno - 1, inter.col_offset
        chars[ii][jj] = "<--" + chars[ii][jj]

        ii, jj = inter.end_lineno - 1, inter.end_col_offset - 1
        chars[ii][jj] = chars[ii][jj] + "-->"

    final = "\n".join(["".join(row) for row in chars])
    return final
