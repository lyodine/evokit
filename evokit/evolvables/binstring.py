from __future__ import annotations

import typing
from typing import Optional, Tuple, TypeVar, List

from ..core import LinearController
from ..core import Evaluator
from ..core import Individual, Population
from ..core import Elitist, SimpleSelector, NullSelector
from ..core import Variator

from typing import Self, Any, Sequence


from random import getrandbits
from random import random


T = TypeVar('T', bound=Individual)


class BinaryString(Individual[List[int]]):
    """A string of bits.
    """
    def __init__(self, value: int, size: int) -> None:
        """
        Args:
            value: length 
        """
        self.genome: int = value
        self.size: int = size

    @staticmethod
    def random(size: int) -> BinaryString:
        return BinaryString(
            getrandbits(size),
            size
        )

    def copy(self: Self) -> Self:
        return type(self)(self.genome, self.size)

    def get(self: Self, pos: int) -> int:
        self._assert_pos_out_of_bound(pos)
        return (self.genome >> pos) & 1

    def set(self: Self, pos: int) -> None:
        self._assert_pos_out_of_bound(pos)
        self.genome |= 1 << pos
        
    def unset(self: Self, pos: int) -> None:
        self._assert_pos_out_of_bound(pos)
        self.genome &= ~(1<<pos)

    def flip(self: Self, pos: int) -> None:
        self._assert_pos_out_of_bound(pos)
        self.genome ^= 1<<pos

    def __str__(self: Self) -> str:
        size: int = self.size
        return str((size * [0] +
                [int(digit) for digit in bin(self.genome)[2:]])[-size:])
    
    def _assert_pos_out_of_bound(self: Self, pos: int)-> None:
        if pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of bound for a binary"
                             f"string of length {self.size}")


class BitDistanceEvaluator(Evaluator[BinaryString]):
    def evaluate(self, s1: BinaryString) -> float:
        return sum(s1.genome)


class NullEvaluator(Evaluator):
    def evaluate(self, s1: Any) -> float:
        return 0


class RandomBitMutator(Variator[BinaryString]):
    def __init__(self, mutation_rate: float):
        if (mutation_rate < 0 or mutation_rate > 1):
            raise ValueError(f"Mutation rate must be within {0} and {1}."
                             f"Got: {mutation_rate}")
        self.mutation_rate = mutation_rate

    def vary(self, parents: Sequence[BinaryString]) -> Tuple[BinaryString, ...]:
        offspring = parents[0].copy()

        for i in range(0, len(offspring.genome)):
            if (random() < self.mutation_rate):
                offspring.genome[i] = 1 if offspring.genome[i] == 0 else 1

        return (offspring,)


if __name__ == "__main__":
    BINSTRING_LENGTH: int = 1000
    POPULATION_SIZE: int = 20
    GENERATION_COUNT: int = 100
    init_pop = Population[BinaryString]()

    for i in range(0, POPULATION_SIZE):
        init_pop.append(BinaryString.random(BINSTRING_LENGTH))

    evaluator = BitDistanceEvaluator()
    pselector = Elitist(SimpleSelector[BinaryString](10))
    cselector = Elitist(SimpleSelector[BinaryString](10))
    variator = RandomBitMutator(0.1)

    ctrl: LinearController = LinearController(
        population=init_pop,
        parent_evaluator=NullEvaluator(),
        parent_selector=NullSelector(),
        variator=variator,
        survivor_evaluator=evaluator,
        survivor_selector=cselector,
    )

    dicts: typing.Dict[int, Optional[float]] = {}

    # from core.accountant import Accountant

    # Ignore type checking. Because `Accountant` is defined for the
    #       `Controller` class, which does not necessarily have one
    #       `population`, type checkers report error on this line.\
    # Because an LinearController is registered with this `Accountant`,
    #       we can be _somewhat_ sure that the accountant's suject has
    #       a `.population`.
    #
    # acc = Accountant({"GENERATION_BEGIN": lambda x: len(x.population)})  # type:ignore

    # ctrl.register(acc)

    for i in range(GENERATION_COUNT):
        ctrl.step()
        dicts[i] = ctrl.population[0].fitness

    print(dicts)

    # print(acc.publish())
