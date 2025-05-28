from __future__ import annotations


from dataclasses import dataclass
from typing import TypeVar
from typing import Literal
from typing import Type
from typing import Any

from ..core import Evaluator
from ..core import Individual, Population
from ..core import Variator

from .algorithms import CanonicalGeneticAlgorithm
from .selectors import Elitist, TruncationSelector
from typing import Self, Sequence

import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional
    from concurrent.futures import ProcessPoolExecutor


@dataclass
class ValueRange:
    """Typing machinery.

    :meta private:

    Represents a range of numbers.
    """
    lo: int
    hi: int


T = TypeVar('T', bound=Individual[Any])


class BinaryString(Individual[int]):
    """A string of bits.

    Tutorial: :doc:`../guides/examples/onemax`.
    """
    def __init__(self, value: int, size: int) -> None:
        """
        Args:
            value: Integer whose binary representation is used.

            size: Length of the binary string
        """
        self.genome: int = value
        self.size: int = size

    @staticmethod
    def random(size: int) -> BinaryString:
        """Return a random binary string.

        Each item in the returned value may be either 1 or 0 with equal
        probability.

        Args:
            size: Size of the generated binary string.
        """
        return BinaryString(
            random.getrandbits(size),
            size
        )

    def copy(self: Self) -> Self:
        """Return a copy of this object.

        Operations performed on the returned value do not affect this object.
        """
        return type(self)(self.genome, self.size)

    def get(self: Self, pos: int) -> Literal[1] | Literal[0]:
        """Return the bit at position :arg:`pos`.

        Args:
            pos: Position of the returned bit value.

        Raise:
            IndexError: If :arg:`pos` is out of range.`
        """
        self._assert_pos_out_of_bound(pos)
        result = (self.genome >> pos) & 1
        return 1 if result == 1 else 0  # To make mypy happy

    def set(self: Self, pos: int) -> None:
        """Set the bit at position :arg:`pos` to 0.

        Args:
            pos: Position of the bit value to set.

        Effect:
            Change :attr:`.genome`.

        Raise:
            IndexError: If :arg:`pos` is out of range.`
        """
        self._assert_pos_out_of_bound(pos)
        self.genome |= 1 << pos

    def clear(self: Self, pos: int) -> None:
        """Set the bit at position :arg:`pos` to 0.

        Args:
            pos: Position of the bit value to clear.

        Effect:
            Change :attr:`.genome`.

        Raise:
            IndexError: If :arg:`pos` is out of range.`
        """
        self._assert_pos_out_of_bound(pos)
        self.genome &= ~(1 << pos)

    def flip(self: Self, pos: int) -> None:
        """Flip the bit at position :arg:`pos`.

        Args:
            pos: Position of the bit value to flip.

        Effect:
            Change :attr:`.genome`.

        Raise:
            IndexError: If :arg:`pos` is outside of range.
        """
        self._assert_pos_out_of_bound(pos)
        self.genome ^= 1 << pos

    def __str__(self: Self) -> str:
        size: int = self.size
        return str((size * [0] + [int(digit)
                                  for digit in bin(self.genome)[2:]])[-size:])

    def to_bit_list(self: Self) -> list[int]:
        """Return a list of bits that represents
        the binary value of :attr:`.genome`.
        """
        size: int = self.size
        return (size * [0] + [int(digit)
                              for digit in bin(self.genome)[2:]])[-size:]

    @classmethod
    def from_bit_list(cls: Type[BinaryString],
                      bit_list: list[int]) -> BinaryString:
        """Return a :class:`.BinaryString` whose :attr:`.genome`
        is the value of bit_list parsed as binary.

        Args:
            bit_list: A string of values ``0`` or ``1``.

        Warn:
            For efficiency, this method does not check if each item in
            :arg:`bit_list` is one of ``1`` and ``0``.

            Effectively, even numbers will be treated as ``1``s whereas
            odd numbers will be treated as ``0``s.
        """
        # Should be efficient, pressing each bit into the genome.
        genome: int = 0
        for bit in bit_list:
            genome = (genome << 1) | bit

        return BinaryString(value=genome,
                            size=len(bit_list))

    def _assert_pos_out_of_bound(self: Self, pos: int) -> None:
        """Assert that an index is within bound of this bit string.

        Args:
            pos: An index.

        Raise:
            IndexError: If :arg:`pos` is not in range ``[0 ... self.size-1]``
        """
        if pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of bound for a binary"
                             f"string of length {self.size}")


class CountBits(Evaluator[BinaryString]):
    """Count the number of ``1`` s.

    Evaluator for :class:`BinaryString`. For each ``1`` in the binary string,
    incur a reward of 1.
    """
    def evaluate(self, individual: BinaryString) -> tuple[float,]:
        return (individual.genome.bit_count(),)


class MutateBits(Variator[BinaryString]):
    """Randomly flip each bit in the parent.

    1-to-1 variator for :class:`.BinaryString`. At each bit in the parent,
    flip it with probability :arg:`mutation_rate``.
    """
    def __init__(self,
                 mutation_rate: float, *,
                 processes: Optional[int | ProcessPoolExecutor] = None,
                 share_self: bool = False):
        """
        Args:
            mutation_rate: Probability to flip each bit in the parent.

        Raise:
            ValueError: If :arg:`mutation_rate` is not in range ``[0,1]``.
        """
        if (mutation_rate < 0 or mutation_rate > 1):
            raise ValueError(f"Mutation rate must be between 0 and 1."
                             f"Got: {mutation_rate}")
        self.arity = 1
        self.mutation_rate = mutation_rate
        self.processes = processes
        self.share_self = share_self

    def vary(self: Self,
             parents: Sequence[BinaryString]) -> tuple[BinaryString, ...]:
        offspring = parents[0].copy()

        for i in range(0, offspring.size):
            if (random.random() < self.mutation_rate):
                offspring.flip(i)

        return (offspring,)


class OnePointCrossover(Variator[BinaryString]):
    """Split and recombine parents.

    2-to-1 variator for :class:`.BinaryString`. Split parents at position
    `k`, then interleave the segments.
    """
    def __init__(self, crossover_probability: float):
        """
        Arg:
            crossover_probability: Probability that crossover is performed.
        """
        self.arity = 2
        if (crossover_probability < 0 or crossover_probability > 1):
            raise ValueError(f"Mutation rate must be between 0 and 1."
                             f"Got: {crossover_probability}")

        self.crossover_probability = crossover_probability

    def vary(self: Self,
             parents: Sequence[BinaryString]) -> tuple[BinaryString, ...]:

        should_perform_crossover: float = random.random()

        if should_perform_crossover < self.crossover_probability:
            # Since integers are not stateful, no need to copy
            p1_genome = parents[0].genome
            p2_genome = parents[1].genome
            size = parents[0].size

            k = random.randrange(size + 1)

            m1 = 2**size - 1
            head_mask = m1 >> (size - k) << (size - k)
            tail_mask = (m1 >> k) & m1

            c1_genome = (p1_genome & head_mask) | (p2_genome & tail_mask)
            c2_genome = (p2_genome & head_mask) | (p1_genome & tail_mask)

            c1 = BinaryString(c1_genome, size=size)
            c2 = BinaryString(c2_genome, size=size)
            return (c1, c2)
        else:
            return (parents[0].copy(),
                    parents[1].copy())


# def _splice_genes(p1_genome: int,
#                   p2_genome: int,
#                   k: int,
#                   size: int):
#     p1_head = p1_genome >> k << k
#     p2_tail = ((p2_genome << k) & 2**size - 1) >> k
#     return p1_head | p2_tail


def trial_run() -> list[BinaryString]:
    BINSTRING_LENGTH: int = 5
    POPULATION_SIZE: int = 100
    GENERATION_COUNT: int = 100

    init_pop = Population[BinaryString](
        [BinaryString.random(BINSTRING_LENGTH)
         for _ in range(POPULATION_SIZE)]
    )

    ctrl: CanonicalGeneticAlgorithm[BinaryString] = CanonicalGeneticAlgorithm(
        population=init_pop,
        variator1=OnePointCrossover(0.8),
        variator2=MutateBits(0.1),
        evaluator=CountBits(),
        selector=Elitist(TruncationSelector[BinaryString](POPULATION_SIZE)),
    )

    bests: list[BinaryString] = []

    for _ in range(GENERATION_COUNT):
        ctrl.step()
        bests.append(ctrl.population.best())
        # Because algorithms are not generic, the type of the population
        #   is not preserved.

    for best_individual in bests:
        print(best_individual.fitness)

    return bests


if __name__ == "__main__":
    trial_run()
