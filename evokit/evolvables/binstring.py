from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import Optional, Tuple, TypeVar, Literal

from ..core import SimpleLinearController
from ..core import Evaluator
from ..core import Individual, Population
from ..core import Elitist, SimpleSelector
from ..core import Variator

from typing import Self, Sequence

import random


@dataclass
class ValueRange:
    """Typing machinery. Represents a range of numbers.

    :meta private:
    """
    lo: int
    hi: int


T = TypeVar('T', bound=Individual)


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
        return str(
            (size * [0] + [int(digit) for digit in bin(self.genome)[2:]])[-size:])

    def _assert_pos_out_of_bound(self: Self, pos: int) -> None:
        """Assert that an index is within bound of this bit string.

        Args:
            pos: An index.

        Raise:
            IndexError: If :arg:`pos` is outside of range :math:`[0, self.size-1]`
        """
        if pos > self.size - 1:
            raise IndexError(f"Index {pos} is out of bound for a binary"
                             f"string of length {self.size}")


class CountBits(Evaluator[BinaryString]):
    """Count the number of ``1`` s.

    Evaluator for :class:`BinaryString`. For each ``1`` in the binary string,
    incur a reward of 1.
    """
    def evaluate(self, s1: BinaryString) -> float:
        return s1.genome.bit_count()


class MutateBits(Variator[BinaryString]):
    """Randomly flip each bit in the parent.

    1-to-1 variator for :class:`.BinaryString`. At each bit in the parent,
    flip it with probability :arg:`mutation_rate``.
    """
    def __init__(self, mutation_rate: float):
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
        self.coarity = 1
        self.mutation_rate = mutation_rate

    def vary(self, parents: Sequence[BinaryString]) -> Tuple[BinaryString, ...]:
        offspring = parents[0].copy()

        for i in range(0, offspring.size):
            if (random.random() < self.mutation_rate):
                offspring.flip(i)

        return (offspring,)


if __name__ == "__main__":
    BINSTRING_LENGTH: int = 1000
    POPULATION_SIZE: int = 10
    GENERATION_COUNT: int = 100
    init_pop = Population[BinaryString]()

    for i in range(0, POPULATION_SIZE):
        init_pop.append(BinaryString.random(BINSTRING_LENGTH))

    evaluator = CountBits()
    selector = Elitist(SimpleSelector[BinaryString](1))
    variator = MutateBits(0.1)

    ctrl: SimpleLinearController = SimpleLinearController(
        population=init_pop,
        variator=variator,
        evaluator=evaluator,
        selector=selector,
    )

    dicts: typing.Dict[int, Optional[float]] = {}

    for i in range(GENERATION_COUNT):
        ctrl.step()
        dicts[i] = ctrl.population[-1].fitness
        print(ctrl.population)

    print(dicts)
