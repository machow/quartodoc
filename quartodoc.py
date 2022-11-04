from griffe.loader import GriffeLoader
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings import dataclasses as ds
from griffe import dataclasses as dc

from dataclasses import dataclass
from tabulate import tabulate

from functools import singledispatch
from plum import dispatch

from typing import Tuple, Union


def parse_function(module: str, func_name: str):
    griffe = GriffeLoader()
    mod = griffe.load_module(module)
    
    f_data = mod.functions[func_name]

    return parse(f_data.docstring, Parser.numpy)


def get_function(module: str, func_name: str, parser: str = "numpy") -> dc.Object:
    """Fetch a function.

    Parameters
    ----------
    module: str
        A module name.
    func_name: str
        A function name.
    parser: str
        A docstring parser to use.

    Examples
    --------
    
    >>> get_function("quartodoc", "get_function")
    <Function('get_function', ...

    """
    griffe = GriffeLoader(docstring_parser = Parser(parser))
    mod = griffe.load_module(module)
    
    f_data = mod.functions[func_name]

    return f_data


# utils =======================================================================
# these largely re-format the output of griffe

def tuple_to_data(el: "tuple[ds.DocstringSectionKind, str]"):
    """Re-format funky tuple setup in example section to be a class."""
    assert len(el) == 2
    
    kind, value = el
    if kind.value == "examples":
        return ExampleCode(value)
    elif kind.value == "text":
        return ExampleText(value)
    
    raise ValueError(f"Unsupported first element in tuple: {kind}")

    
@dataclass
class ExampleCode:
    value: str


@dataclass
class ExampleText:
    value: str

    
def escape(val: str):
    return f"`{val}`"

# to_md =======================================================================
# griffe function dataclass structure:
#   Object:
#     kind: Kind {"module", "class", "function", "attribute"}
#     name: str
#     docstring: Docstring
#     parent
#     path, canonical_path: str
#
#   Alias: wraps Object (_target) to lookup properties
#
#   Module, Class, Function, Attribute
#
# griffe docstring dataclass structure:
#   DocstringSection -> DocstringSection*
#   DocstringElement -> DocstringNamedElement -> Docstring*
#
#
# example templates:
#   https://github.com/mkdocstrings/python/tree/master/src/mkdocstrings_handlers/python/templates


class MdRenderer:
    def __init__(self, header_level:int=2, show_signature:str=True, hook_pre=None):
        self.header_level = header_level
        self.show_signature = show_signature
        self.hook_pre = hook_pre

    @dispatch
    def to_md(self, el):
        raise NotImplementedError(f"Unsupported type: {type(el)}")

    @dispatch
    def to_md(self, el: Union[dc.Alias, dc.Object]):                                              
        # TODO: replace hard-coded header level                                     
                                                                                    
        _str_pars = self.to_md(el.parameters)                                            
        str_sig = f"{el.name}({_str_pars})"                                      
                                                                                    
        str_title = f"{'#' * self.header_level} {el.name}"
        str_body = list(map(self.to_md, el.docstring.parsed))                            
                                                                                    
        if self.show_signature:
            parts = [str_title, str_sig, *str_body]
        else:
            parts = [str_title, *str_body]
        
        return "\n\n".join(parts)                           
                                                                                
                                                                                
    # signature parts ------------------------------------------------------------- 
                                                                                
    @dispatch
    def to_md(self, el: dc.Parameters):                                                       
        return ", ".join(map(self.to_md, el))                                            
                                                                                    
                                                                                    
    @dispatch
    def to_md(self, el: dc.Parameter):                                                        
        # TODO: missing annotation                                                  
        splats = {dc.ParameterKind.var_keyword, dc.ParameterKind.var_positional}    
        has_default = el.default and el.kind not in splats                          
                                                                                    
        if el.annotation and has_default:                                           
            return f"{el.name}: {el.annotation} = {el.default}"                     
        elif el.annotation:                                                         
            return f"{el.name}: {el.annotation}"                                    
        elif has_default:                                                           
            return f"{el.name}={el.default}"                                        
                                                                                    
        return el.name                                                              
                                                                                    
                                                                                    
    # docstring parts ------------------------------------------------------------- 
                                                                                    
    @dispatch                                                                 
    def to_md(self, el: ds.DocstringSectionText):                                             
        return el.value                                                             
                                                                                    
                                                                                    
    # parameters ----                                                               
                                                                                    
    @dispatch
    def to_md(self, el: ds.DocstringSectionParameters):                                       
        rows = list(map(self.to_md, el.value))                                           
        header = ["Name", "Type", "Description", "Default"]                         
        return tabulate(rows, header, tablefmt="github")                            
                                                                                    
    @dispatch                                                                
    def to_md(self, el: ds.DocstringParameter) -> Tuple[str]:                                 
        # TODO: if default is not, should return the word "required" (unescaped)    
        default = "required" if el.default is None else escape(el.default)          
        annotation = el.annotation.full if el.annotation else None
        return (escape(el.name), annotation, el.description, default)            
                                                                                    
    # examples ----                                                                 
                                                                                    
    @dispatch                                                                 
    def to_md(self, el: ds.DocstringSectionExamples):                                         
        # its value is a tuple: DocstringSectionKind["text" | "examples"], str      
        data = map(tuple_to_data, el.value)                                         
        return "\n\n".join(list(map(self.to_md, data)))                                  
                                                                                    
                                                                                    
    @dispatch                                                                 
    def to_md(self, el: ExampleCode):                                                         
        return f"""
```python
{el.value}
```\
"""                                                                             
                                                                                    
                                                                                    
    @dispatch                                                                
    def to_md(self, el: ExampleText):                                                         
        return el.value                                                             
                                                                                    
    @dispatch.multi(
        (ds.DocstringAdmonition,),
        (ds.DocstringDeprecated,),
        (ds.DocstringRaise,),
        (ds.DocstringWarn,),
        (ds.DocstringReturn,),
        (ds.DocstringYield,),
        (ds.DocstringReceive,),
        (ds.DocstringAttribute,),
    )
    def to_md(self, el):
        raise NotImplementedError(f"{type(el)}")
