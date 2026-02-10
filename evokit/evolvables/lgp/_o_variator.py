from .._common import crossover
from typing import override
from typing import Sequence
from typing import Self
from ...core import Variator
from ._o_individual import LinearGeneticProgram


class Crossover(Variator[LinearGeneticProgram]):
    @override
    def __init__(self: Self,
                 k: int,
                 allow_repeat: bool = True,
                 even: bool = True) -> None:
        """
        Args:
            k: The number of crossover points.

            allow_repeat: If ``True``, then crossover segments
                can be empty. Swapping any segment with an empty
                segment effectively moves it to the empty segment's
                index.

            even: If ``True``, then crossover segments must have the
                same size and each offspring has the same size as its
                "direct" parent (parent where the offspring takes its
                first segment from). Otherwise, offspring can have
                different lengths.
        """
        # Args were copied from _common.crossover.
        self.k = k
        self.arity = 2
        self.allow_repeat = allow_repeat
        self.even = even

    @override
    def vary(self, parents: Sequence[LinearGeneticProgram])\
            -> tuple[LinearGeneticProgram, LinearGeneticProgram]:
        """Required.

        Produce new individuals from existing ones.

        Because `.arity=1` in the initialiser, `parents`
        will be a 1-tuple at runtime.
        """
        res_1, res_2 = crossover(
            seq_1=[x.copy() for x in parents[0].genome],
            seq_2=[x.copy() for x in parents[1].genome],
            k=self.k,
            allow_repeat=self.allow_repeat,
            even=self.even
        )

        return (LinearGeneticProgram(res_1),
                LinearGeneticProgram(res_2))
