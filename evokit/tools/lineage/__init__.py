from ...core import Variator, Individual
from typing import TypeVar
from typing import Any
from typing import Callable
from typing import Sequence
from typing import Protocol
from typing import Generic
from typing import Self
from typing import Optional
from functools import wraps
from types import MethodType
import graphviz  # type: ignore[import-untyped]
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

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

    .. warning::

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


def uid(x: Individual) -> str:
    return str(x.uid)


def graph_lineage(individuals: Sequence[Individual],
                  identifier: Callable[[Individual], str] = uid,
                  use_tooltip: bool = False,
                  vertical_spacing: int = 1,
                  save_as: "Optional[Path | str]" = None)\
        -> graphviz.Digraph:
    """Graph the lineage of an individual. This information
    can be accessed as :attr:`.Individual.parents`.

    Linage tracking is off by default. :meth:`TrackParents`
    enables lineage tracking in a variator.

    Args:
        individuals: Individuals to plot.

        identifier: A function to convert an individual to
            a unique identifier. The default :meth:`id` is
            efficient but might not work with individual
            that have moved out of memory (for example, ones
            that have been :meth:`.Individual.load`\\ ed)

        use_tooltip: If ``True``, then the name (string
            representation) of each node is rendered
            as a tooltip instead of text. Tooltips
            are only rendered in SVG files

        vertical_spacing: Multiplier for vertical spacing
            between nodes.

        save_as: Path to save the output as. If `name` is
            given, file will be saved as `name.svg`.

            .. warning::
                `save_as` can traverse to parent directories
                and overwrite files.
    """
    dot = graphviz.Digraph()
    # 0.5 is the default ranksep (vertical spacing between nodes)
    dot.attr(ranksep=str(vertical_spacing * 0.5))

    edge_dict: dict[str, tuple[str, set[str]]] = {}

    for ind in individuals:
        if use_tooltip:
            dot.node(identifier(ind), " ", tooltip=str(ind), shape="point")
        else:
            dot.node(identifier(ind), str(ind), shape="rectangle")

        register_parents(edge_dict,
                         ind,
                         identifier)

    for source, (source_repr, targets) in edge_dict.items():
        if use_tooltip:
            dot.node(source, " ", tooltip=source_repr, shape="point")
        else:
            dot.node(source, source_repr, shape="rectangle")

            dot.node(source, source_repr)
        for target in targets:
            dot.edge(source, target, arrowhead="none")

    if save_as is not None:
        dot.render(filename=save_as, format="svg")

    return dot
