ident = 0
def dispatch_ident()-> str:
    global ident
    return "a" + str(*(ident:=ident+1,))

import graphviz
from typing import Callable

def p2dot(gp, dispatcher: Callable[[], str] = dispatch_ident):
    expr = gp.genome
    my_name: str = expr.value.__name__ if callable(expr.value) else str(expr.value)
    my_ident = dispatcher()
    dot = graphviz.Digraph('square-peg', comment='The Square Peg')
    dot.node(my_ident, my_name)

    for each_child in expr.children:
        p2dot_recurse(each_child, dot, my_ident, dispatcher)

    return dot
         
def p2dot_recurse(expr, dot, parent_ident, dispatcher: Callable[[], str]): 
    my_name: str = expr.value.__name__ if callable(expr.value) else str(expr.value)
    my_ident = dispatcher()

    dot.node(my_ident, my_name)
    dot.edge(parent_ident, my_ident)

    for each_child in expr.children:
        p2dot_recurse(each_child, dot, my_ident, dispatcher)