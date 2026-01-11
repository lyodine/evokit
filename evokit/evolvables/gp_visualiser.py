# mypy: disable-error-code="import-untyped,no-any-unimported"
from graphviz import Digraph

from .gp import Expression

from typing import Callable
from typing import Any
from .gp import Program
from .._utils.dependency import ensure_installed

#: Global counter of the number of dispatched identifiers.
ident = 0

ensure_installed("graphviz")


def _dispatch_ident() -> str:
    """Return an unique identifier.

    During the same runtime, each call of this method returns a
    different identifier.
    """
    global ident
    return "a" + str(*(ident := ident + 1,))


def p2dot(gp: Program[Any],
          dispatcher: Callable[[], str] = _dispatch_ident) -> Digraph:
    """Visualise a tree-based genetic program.

    Return a :class:`graphviz.Digraph` that represents the given tree-based
    genetic program.

    Args:
        gp: Genetic program to visualise.

        dispatcher: :class:`Callable` that should return a unique

        identifier when called.
    """
    expr: Expression[Any] = gp.genome
    my_name: str = expr.value.__name__ if callable(expr.value)\
        else str(expr.value)
    my_ident: str = dispatcher()
    dot: Digraph = Digraph("GP Visualisation")
    dot.node(my_ident, my_name)  # type: ignore[reportUnknownMemberType]

    for each_child in expr.children:
        _p2dot_recurse(each_child, dot, my_ident, dispatcher)

    return dot


def _p2dot_recurse(expr: Expression[Any],
                   dot: Digraph,
                   parent_ident: str,
                   dispatcher: Callable[[], str]) -> None:
    """Recursive function that builds the visualisation.

    Recursively add nodes to a :class:`graphviz.Digraph`, then return it.

    Args:
        expr: An :class:`.Expression`

        dot: A :class:`graphviz.Digraph`

        parent_ident: Identifier of the parent node

        dispatcher: :class:`Callable` that should return a unique
        identifier when called.
    """
    my_name: str = expr.value.__name__ if callable(expr.value)\
        else str(expr.value)
    my_ident: str = dispatcher()

    dot.node(my_ident, my_name)  # type: ignore[reportUnknownMemberType]
    dot.edge(parent_ident, my_ident)  # type: ignore[reportUnknownMemberType]

    for each_child in expr.children:
        _p2dot_recurse(each_child, dot, my_ident, dispatcher)
