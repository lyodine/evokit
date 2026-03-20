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
import matplotlib as mpl
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


# child_parent_links follows this structure:
#   source identifier (hash or memory address):
#       representation, fitness, {target identifiers}
def register_parents[D](child_parent_links: dict[str,
                                                 tuple[str,
                                                       float,
                                                       set[str]]],
                        ind: Individual[D],
                        identifier: Callable[[Individual[D]],
                                             str]):
    my_id = identifier(ind)
    if my_id not in child_parent_links:
        child_parent_links[my_id] = (str(ind),
                                     ind.fitness[0],
                                     set())

    if ind.parents is not None:
        for parent in ind.parents:
            parent_id = identifier(parent)
            if parent_id not in child_parent_links[my_id]:
                child_parent_links[my_id][2].add(parent_id)

            register_parents(child_parent_links,
                             parent,
                             identifier)


def uid(x: Individual) -> str:
    return str(x.uid)


def _normalise_fitness(fitness: float,
                       maxf: float,
                       minf: float):
    """Given a max and a min fitness,
    return a value in range [0...1].
    """
    return (fitness - minf) / (maxf - minf)


def graph_lineage(individuals: Sequence[Individual],
                  identifier: Callable[[Individual], str] = uid,
                  compact: bool = False,
                  use_colour: bool = True,
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

        compact: If ``True``, then (a) render each node
            as a dot and (b) render the content of that node
            as a tooltip. Tooltips are only rendered in SVG files

        use_colour: If ``True``, then render each node with
            a colour that indicates its fitness. Green means good;
            red means bad.

        vertical_spacing: Multiplier for vertical spacing
            between nodes.

        save_as: Path to save the output as. If `name` is
            given, file will be saved as `name.svg`.

            .. warning::
                `save_as` can traverse has the potential to traverse
                to parent directories and overwrite files.
    """
    dot = graphviz.Digraph()
    # 0.5 is the default ranksep (vertical spacing between nodes)
    dot.attr(ranksep=str(vertical_spacing * 0.5))

    edge_dict: dict[str, tuple[str,
                               float,
                               set[str]]] = {}

    for ind in individuals:
        # if use_tooltip:
        #     dot.node(identifier(ind), " ", tooltip=str(ind), shape="point")
        # else:
        #     dot.node(identifier(ind), str(ind), shape="rectangle")

        register_parents(edge_dict,
                         ind,
                         identifier)

    max_fitness: float = -float("inf")
    min_fitness: float = float("inf")
    # Colourised layout
    for _, (_, fitness, _) in edge_dict.items():
        max_fitness = max(fitness, max_fitness)
        min_fitness = min(fitness, min_fitness)

    for source, (source_repr, fitness, targets) in edge_dict.items():
        fitness_color: str | None = None
        if use_colour:
            fitness_intensity: float = _normalise_fitness(
                fitness=fitness,
                maxf=max_fitness,
                minf=min_fitness,
            )

            fitness_color = mpl.colors.to_hex(
                # Suppressing error. matplotlib.colormaps
                #   exists, but the linter can't find it.
                mpl.colormaps['RdYlGn'](fitness_intensity)  # type: ignore
            )

        if compact:
            dot.node(source,
                     " ",
                     tooltip=source_repr,
                     shape="point",
                     height="0.08",
                     width="0.08",
                     fixedheight="yes",
                     color="#696969",  # HTML DimGrey
                     fillcolor=fitness_color
                     if fitness_color is not None
                     else "black")
        else:
            dot.node(source,
                     source_repr,
                     shape="rectangle",
                     color=fitness_color
                     if fitness_color is not None
                     else "#696969")
        for target in targets:
            # `dir` needs to be `back` because
            #   each item in `edge_dict` maps the
            #   child to parents.
            dot.edge(source, target,
                     dir="back",
                     arrowhead="normal",
                     tailclip="true",
                     arrowsize="0.2",
                     tooltip=" ",
                     color="#696969")

    if save_as is not None:
        base_dir = Path().resolve()
        target_dir = Path(save_as).resolve()

        if not target_dir.is_relative_to(base_dir):
            raise ValueError(f"Target directory {target_dir} not"
                             f" relative to base directory {base_dir}."
                             " Aborting.")

        dot.render(filename=save_as, format="svg")

    return dot
