from __future__ import annotations

import typing
from typing import Optional, Tuple, TypeVar, List

from core.controller import LinearController
from core.evaluator import Evaluator
from core.population import Individual, Population
from core.selector import Elitist, SimpleSelector, NullSelector
from core.variator import Variator

from typing import Self, Any, Sequence


from random import getrandbits
from random import random


T = TypeVar('T', bound=Individual)


class BinaryString(Individual[List[int]]):
    def __init__(self, value: List[int]) -> None:
        self.genome: List[int] = value

    @staticmethod
    def random(len: int) -> BinaryString:
        return BinaryString(
            (len * [0] +
                [int(digit) for digit in bin(getrandbits(len))[2:]])[-len:]
        )

    def copy(self: Self) -> Self:
        return type(self)(self.genome.copy())

    def __str__(self: Self) -> str:
        return str(self.genome)


class BitDistanceEvaluator(Evaluator[BinaryString]):
    def evaluate(self, s1: BinaryString) -> float:
        return sum(s1.genome)


class NullEvaluator(Evaluator):
    def evaluate(self, s1: Any) -> float:
        return 0


class RandomBitMutator(Variator[BinaryString]):
    def __init__(self, mutation_rate: float):
        super().__init__(1)
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
    BINSTRING_LENGTH: int = 20
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
        parent_evaluator=evaluator,
        parent_selector=pselector,
        variator=variator,
        survivor_evaluator=NullEvaluator(),
        survivor_selector=NullSelector(),
    )

    dicts: typing.Dict[int, Optional[float]] = {}

    from core.accountant import Accountant

    # Ignore type checking. Because `Accountant` is defined for the
    #       `Controller` class, which does not necessarily have one
    #       `population`, type checkers report error on this line.\
    # Because an LinearController is registered with this `Accountant`,
    #       we can be _somewhat_ sure that the accountant's suject has
    #       a `.population`.
    #
    acc = Accountant({"GENERATION_BEGIN": lambda x: len(x.population)})  # type:ignore

    ctrl.register(acc)

    for i in range(GENERATION_COUNT):
        ctrl.step()
        dicts[i] = ctrl.population[0].fitness

    print(dicts)

    print(acc.publish())
