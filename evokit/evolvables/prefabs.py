from evokit.core import Population
from evokit.evolvables.algorithms import SimpleLinearAlgorithm
from evokit.evolvables.selectors import TruncationSelector, Elitist
from evokit.evolvables.binstring import BinaryString, CountBits, MutateBits
from evokit.tools.lineage import TrackParents
from inspect import signature

"""So, this global variable, ahh... fetches the default value
of :arg:`max_parents` in TrackParents's constructor. Because
apparently Python lets you do that.
"""
_TRACK_PARENTS_MAX_PARENTS_DEFAULT: int =\
    [para.default
     for para in signature(TrackParents).parameters.values()
     if para.name == "max_parents"][0]


def make_algo(ind_size: int,
              pop_size: int,
              mutate_p: float,
              max_parents=_TRACK_PARENTS_MAX_PARENTS_DEFAULT)\
        -> SimpleLinearAlgorithm[BinaryString]:
    """Create a simple elitist onemax algorithm that tracks
    5 generations of parents.

    Useful for playing around with features.
    """
    pop: Population[BinaryString] = Population(
        BinaryString.random(ind_size) for _ in range(pop_size))
    return SimpleLinearAlgorithm(population=pop,
                                 variator=TrackParents(
                                     MutateBits(mutate_p),
                                     max_parents=max_parents),
                                 evaluator=CountBits(),
                                 selector=Elitist(
                                     TruncationSelector(pop_size)))
