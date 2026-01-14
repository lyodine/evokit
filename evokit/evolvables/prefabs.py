from evokit.core import Population
from evokit.evolvables.algorithms import SimpleLinearAlgorithm
from evokit.evolvables.selectors import TruncationSelector, Elitist
from evokit.evolvables.bitstring import BitString, CountBits, MutateBits
from evokit.tools.lineage import TrackParents
from evokit._utils.inspect import get_default_value
from typing import TYPE_CHECKING
from typing import Optional

if TYPE_CHECKING:
    from concurrent.futures import ProcessPoolExecutor


"""So, this global variable, ahh... fetches the default value
of :arg:`max_parents` in TrackParents's constructor. Because
apparently Python lets you do that.

So I'm doing something that I'm not really supposed to, and
making it a function so that I can do it again.
"""
_TRACK_PARENTS_MAX_PARENTS_DEFAULT: int =\
    get_default_value(TrackParents, "max_parents")

_BITSTRING_PROCESSES_DEFAULT: "Optional[int | ProcessPoolExecutor]" =\
    get_default_value(MutateBits, "processes")


def make_onemax(pop_size: int,
                ind_size: int,
                mutate_p: float,
                processes: "Optional[int | ProcessPoolExecutor]" =
                _BITSTRING_PROCESSES_DEFAULT,
                max_parents=_TRACK_PARENTS_MAX_PARENTS_DEFAULT)\
        -> SimpleLinearAlgorithm[BitString]:
    """Create a simple elitist onemax algorithm that tracks
    5 generations of parents.

    Useful for playing around with features.
    """
    pop: Population[BitString] = Population(
        BitString.random(ind_size) for _ in range(pop_size))
    return SimpleLinearAlgorithm(population=pop,
                                 variator=TrackParents(
                                     MutateBits(mutate_p, processes=processes),
                                     max_parents=max_parents),
                                 evaluator=CountBits(),
                                 selector=Elitist(
                                     TruncationSelector(pop_size)))
