from ...core import Individual
from ._program import Instruction
from typing import Self, override


class LinearGeneticProgram(Individual[list[Instruction]]):
    """A Linear genetic program. This program consists of
    a sequence of instructions, which in turn act on registers.

    Not to be confused with LGP,
    which means linear genetic programming.
    """
    def __init__(self: Self,
                 program: list[Instruction]):
        self.genome = program

    @override
    def copy(self: Self) -> Self:
        return type(self)([x.copy() for x in self.genome])
