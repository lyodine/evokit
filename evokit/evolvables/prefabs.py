from evokit.core import Population
from evokit.evolvables.algorithms import SimpleLinearAlgorithm
from evokit.evolvables.selectors import TruncationSelector, Elitist
from evokit.evolvables.binstring import BinaryString, CountBits, MutateBits
from evokit.tools.lineage import TrackParents


def make_algo(ind_size: int,
              pop_size: int,
              mutate_p: float) -> SimpleLinearAlgorithm[BinaryString]:
    """Create a simple elitist onemax algorithm that tracks
    5 generations of parents.

    Useful for playing around with features.
    """
    pop: Population[BinaryString] = Population(
        BinaryString.random(ind_size) for _ in range(pop_size))
    return SimpleLinearAlgorithm(population=pop,
                                 variator=TrackParents(MutateBits(mutate_p)),
                                 evaluator=CountBits(),
                                 selector=Elitist(
                                     TruncationSelector(pop_size)))
