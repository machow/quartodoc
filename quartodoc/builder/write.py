from plum import dispatch
from quartodoc.autosummary import Builder


@dispatch
def write_doc_pages(builder: Builder):
    return builder.write_doc_pages()


@dispatch
def write_index(builder: Builder):
    return builder.write_index()


@dispatch
def build(builder: Builder):
    return builder.build()
