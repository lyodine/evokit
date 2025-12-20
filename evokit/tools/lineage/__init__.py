from evokit.core import Variator, Individual
from typing import TypeVar
from typing import Any
from typing import Callable
from typing import Sequence
from typing import Protocol
from typing import Generic
from typing import Self
from functools import wraps
from types import MethodType
import graphviz  # type: ignore[import-untyped]

D = TypeVar("D", bound=Individual[Any])


class VarySignature(Protocol, Generic[D]):
    """Signature of :meth:`.Variator.vary`.

    :meta private
    """
    def __call__(self: Self,
                 me: Variator[D],
                 parents: Sequence[D],
                 *args: Any,
                 **kwargs: Any) -> tuple[D, ...]:
        ...


def TrackParents(var: Variator[D],
                 max_parents: int = 5) -> Variator[D]:
    """Decorator that lets a variator track the lineage
    of an offspring.

    In particular, each call to :python:`var.vary` sets
    the :attr:`.Individual.parents` of all offspring to
    its inputs.

    Warn:
        To save cost, the :attr:`.Individual.parents` is reset to
        :python:`None` after an individual ever becomes the
        :attr:`max_parents` \\ :sup:`th` parent of another individual.

        If an individual is preserved for several generations,
        its :attr:`.Individual.parents` may be expunged.

    """
    def wrap_function(custom_vary: VarySignature[D])\
            -> VarySignature[D]:

        @wraps(custom_vary)
        def wrapper(me: Variator[D],
                    parents: Sequence[D],
                    *args: Any, **kwargs: Any) -> tuple[D, ...]:
            """Context that implements elitism.
            """

            # Acquire results of the original selector
            results: tuple[D, ...] = \
                custom_vary(me, parents, *args, **kwargs)

            for res in results:
                res.set_parents(tuple(parents), max_parents)

            return results
        return wrapper

    setattr(var, 'vary',
            MethodType(
                wrap_function(var.vary.__func__),  # type:ignore
                var))
    return var


# source_target_links follows this structure:
#   source identifier (hash or memory address):
#       representation, {target identifiers}
def register_parents[D](source_target_links: dict[str, tuple[str, set[str]]],
                        ind: Individual[D],
                        identifier: Callable[[Individual[D]],
                                             str]):
    my_id = identifier(ind)
    if my_id not in source_target_links:
        source_target_links[my_id] = (str(ind), set())

    if ind.parents is not None:
        for parent in ind.parents:
            parent_id = identifier(parent)
            if parent_id not in source_target_links[my_id]:
                source_target_links[my_id][1].add(parent_id)

            register_parents(source_target_links,
                             parent,
                             identifier)


def graph_lineage(individuals: Sequence[Individual],
                  identifier: Callable[[Individual],
                                       str] = lambda x: str(id(x)))\
        -> graphviz.Digraph:
    """Graph the lineage of an individual. This information
    can be accessed as :attr:`.Individual.parents`.

    Linage tracking is off by default. :meth:`TrackParents`
    enables lineage tracking in a variator.

    Args:
        individuals: individuals to plot.

        identifier: A function to convert an individual to
            a unique identifier. The default :meth:`id` is
            efficient but might not work with individual
            that have moved out of memory (for example, )
    """
    dot = graphviz.Digraph()

    edge_dict: dict[str, tuple[str, set[str]]] = {}

    for ind in individuals:
        dot.node(identifier(ind), str(ind))
        register_parents(edge_dict,
                         ind,
                         identifier)

    for source, (source_repr, targets) in edge_dict.items():
        dot.node(source, source_repr)
        for target in targets:
            dot.edge(source, target)

    return dot
