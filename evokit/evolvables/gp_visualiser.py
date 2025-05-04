from graphviz import Digraph

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Callable
    from gp import Program
    from gp import Expression

#: Global counter of the number of dispatched identifiers.
ident = 0

def _dispatch_ident()-> str:
    """Return an unique identifier.
    
    During the same runtime, each call of this method returns a
    different identifier.
    """
    global ident
    return "a" + str(*(ident:=ident+1,))


def p2dot(gp: Program, dispatcher: Callable[[], str] = _dispatch_ident) -> Digraph:
    """Visualise a tree-based genetic program.

    Return a :class:`graphviz.Digraph` that represents the given  tree-based
    genetic program as a tree.
    """
    expr: Expression = gp.genome
    my_name: str = expr.value.__name__ if callable(expr.value) else str(expr.value)
    my_ident: str = dispatcher()
    dot: Digraph = Digraph("GP Visualisation")
    dot.node(my_ident, my_name)

    for each_child in expr.children:
        _p2dot_recurse(each_child, dot, my_ident, dispatcher)

    return dot


def _p2dot_recurse(expr, dot, parent_ident, dispatcher: Callable[[], str])-> None:
    """
    """
    my_name: str = expr.value.__name__ if callable(expr.value) else str(expr.value)
    my_ident: str = dispatcher()

    dot.node(my_ident, my_name)
    dot.edge(parent_ident, my_ident)

    for each_child in expr.children:
        _p2dot_recurse(each_child, dot, my_ident, dispatcher)