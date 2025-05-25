# mypy: ignore-errors
# flake8: noqa

from __future__ import annotations\

import numpy as np

from typing import Annotated, Sequence, Any

# It's just so appropriate here.
from abc import ABC

from functools import singledispatch
class Instruction():
    pass


from abc import abstractmethod

from dataclasses import dataclass

from typing import override


class StructureType(ABC):
    """Type of a control structure

    Apparently the "actual" control structure \
    """
    @abstractmethod
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction])-> None:
        """Invoke instructions in the context of a linear program.
        """

class StructureScope(ABC):
    """Control structure.

    To define a control structure, specify its type (as a :class:`StructureType`),
    then initialise a :class:`StructureScope` with that type.
    """
    @abstractmethod
    def __init__(self: Self,
                 stype: StructureType,
                 *args: Any,
                 **kwargs: Any)-> None:
        """
        Args:
            stype: Type of the control structure, such as :class:`If`
                and :class:`While`.
        """


class StructOverLines(StructureScope):
    """A control structure that spans multiple lines.
    """
    def __init__(self: Self, stype: StructureType, line_count: int)-> None:
        """
        Args:
            stype: Type of the control structure.
            line_count: Number of lines that this control structure spans.
        """
        self.stype: StructureType = stype
        self.line_count: int = line_count


class StructUntilLabel(StructureScope):
    """A control structure that extends to the given label.
    """
    def __init__(self: Self, stype: StructureType, label: str):
        """
        Args:
            stype: Type of the control structure.
            label: Text of label that terminates this control structure.
        """
        self.stype: StructureType = stype
        self.label: str = label

class StructNextLine(StructureScope):
    """Control structure that spans one line.
    """
    def __init__(self: Self, stype: StructureType):
        """
        Args:
            stype: Type of the control structure.
        """
        self.stype: StructureType = stype

class Label():
    """Just a label. A label should be identified by its text.
    """
    def __init__(self: Self, label: str):
        """
        Args:
            label: Text of the label.
        """
        self.label = label

class For(StructureType):
    """Simple \"for\" loop.

    A control structure with this type repeats :arg:`count` times.
    """
    def __init__(self: Self, count: int):
        self.count = count

    @override
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        for _ in range(self.count):
            lgp.run(instructions)

WHILE_LOOP_CAP = 20

class While(StructureType):
    """\"While\" loop.

    A control structure with this type repeats until :arg:`conditional`
    is satisfied.
    """
    def __init__(self: Self, conditional: Condition):
        """
        Arg:
            conditional: Condition that, if satisfied, ends the structures.
        """
        self.conditional = conditional

    @override
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        for _ in range(WHILE_LOOP_CAP):
            if (lgp.check(self.conditional)):
                lgp.run(instructions)
            else:
                break

class If(StructureType):
    """\"if\" conditional.

    A control structure with this type executes only if :arg:`conditional`
    is satisfied.
    """
    def __init__(self: Self, conditional: Condition):
        self.conditional = conditional

    @override
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        if (lgp.check(self.conditional)):
                lgp.run(instructions)

@dataclass
class ValueRange:
    min: float
    max: float

from dataclasses import dataclass
from typing import Tuple
from typing import Self
from typing import Callable


@dataclass
class Operation(Instruction):
    """An algebraic operation.

    Call :arg:`function` with :arg:`args` as arguments.
    Assign the result to the register at position :arg:`target`.

    The argument :arg:`args` can index constants and registers.
    Registers start at index 0; constants are represented as negative
    numbers starting at index -1.
    """
    def __init__(self: Self,
                 function: Callable[..., float],
                 target: Annotated[int, ValueRange(0, float('inf'))],
                 args: Tuple[int, ...]):
        """
        todo
        """
        self.function: Callable[..., float] = function
        self.target: int = target
        self.args: Tuple[int, ...] = args

        # If true, then operands are all constants. Apparently a bad thing
        #   according to the Banzhaf LGP book.
        # If this is the case, raise an warning.
        has_no_register_operand: bool = True

        for reg in args:
            if reg >= 0:
                has_no_register_operand = False

        if (has_no_register_operand):
            raise ValueError(f"Operand registers are all constants")

    def __str__(self: Self):
        args: str = ', '.join((f"r[{x}]" if x >= 0 else f"c[{-x-1}]" for x in self.args))
        function_name: str = getattr(self.function,
                                     '__name__',
                                     repr(self.function))

        return f"r[{self.target}] <- {function_name}({args})"

    __repr__ = __str__

class Condition():
    """Abstract base class for predicates, or conditions.

    Conditions are used by conditional control structures, such as
    :class:`If` and :class:`While`.
    """
    def __init__(self: Self,
                 function: Callable[..., bool],
                 args: Tuple[int, ...]):
        """
        Args:
            function: todo
            args: todo
        """
        self.function = function
        self.args = args


from typing import Self

from numbers import Number

from typing import TypeVar, Generic
T = TypeVar("T")

from typing import List

from numpy.typing import NDArray

from numpy import float64

class LinearProgram():
    def __init__(self: Self,
                 coarity: int,
                 inputs: Sequence[float],
                 input_can_change: bool,
                 reg_length: int,
                 constants: Sequence[float],
                 initialiser: float | Callable[[], float]):

        #: Number of output registers
        self.coarity: int
        self.coarity = coarity

        self.registers: NDArray[np.float64]

        self.constants: NDArray[np.float64]

        if isinstance(initialiser, Number):
            self.registers = np.full(reg_length, initialiser, dtype=float64)
        elif (callable(initialiser)):
            self.registers = np.empty(reg_length, dtype=float64)
            for i in range(len(self.registers)):
                self.registers[i] = initialiser()
        else:
            raise ValueError("Initialiser is not callable and not a value.")

        # Initialise constants
        self.constants = np.fromiter(constants, dtype=float64)
        self.constants.flags.writeable = False

        # Append input registers to either constants or registers
        if input_can_change:
            self.registers = np.append(self.registers, inputs)
        else:
            self.constants = np.append(self.constants, inputs)

    def run(self: Self, instructions: Sequence[Instruction]) -> NDArray[np.float64]:
        current_line: int = 0

        while current_line < len(instructions):
            current_line += self.run_instruction(instructions[current_line], instructions, current_line)

        return self.get_output_values()

    def get_output_values(self: Self) -> NDArray[np.float64]:
        return self.registers[:self.coarity]

    def check(self: Self, cond: Conditional) -> bool:
        return cond.function(*(self.constants[-i-1] if i < 0 else self.registers[i]\
                      for i in cond.args))


    def run_instruction(self: Self, instruction: Instruction,
                        instructions: Sequence[Instruction],
                        pos: int) -> int:
        match instruction:
            case Operation():
                return self._run_operation(instruction)
            case StructNextLine():
                return self._run_struct_next_line(instruction, instructions, pos)
            case StructOverLines():
                return self._run_struct_over_lines(instruction, instructions, pos)
            case StructUntilLabel():
                return self._run_struct_until_label(instruction, instructions, pos)
            case Label():
                return self._run_label()
            case _:
                raise ValueError(f"Instruction type {type(instruction).__name__} Not recognised")

    def _run_label(self: Self) -> int:
        return 1

    def _run_operation(self: Self, instruction: Operation) -> int:
        if instruction.target < 0:
            raise ValueError(f"Malformed instruction: assignment to c[{-instruction.target-1}]")
        else:
            self.registers[instruction.target] =\
                instruction.function(
                    *(self.constants[-i-1] if i < 0 else self.registers[i]\
                      for i in instruction.args))
        print(str(instruction))
        return 1

    def _run_struct_over_lines(self: Self, instruction: StructOverLines,
                               instructions: Sequence[Instruction],
                               pos: int) -> int:
        collected_lines: List[Instruction] = []
        current_pos: int = pos+1

        num_of_steps: int = min([len(instructions) - current_pos, instruction.line_count])


        for _ in range(num_of_steps-1):
            print(f"Collect command into structure: {instructions[current_pos]}")
            collected_lines.append(instructions[current_pos])
            current_pos += 1

        instruction.stype(self, collected_lines)

        return num_of_steps

    def _run_struct_next_line(self: Self, instruction: StructOverLines,
                              instructions: Sequence[Instruction],
                              pos: int) -> int:

        collected_lines: List[Instruction] = []
        current_pos: int = pos+1

        num_of_steps: int = min([len(instructions) - current_pos, 1])

        for _ in range(num_of_steps):
            collected_lines.append(instructions[current_pos])
            current_pos += 1
        instruction.stype(self, collected_lines)


        return num_of_steps

    def _run_struct_until_label(self: Self, instruction: StructUntilLabel,
                                instructions: Sequence[Instruction],
                                pos: int) -> int:

        collected_lines: List[Instruction] = []
        current_pos: int = pos+1

        num_of_steps: int = len(instructions) - current_pos

        for _ in range(num_of_steps):
            current_instruction: Instruction = instructions[current_pos]

            if (isinstance(current_instruction, Label) and current_instruction.label == instruction.label):
                current_pos += 1
                break
            else:
                collected_lines.append(instructions[current_pos])
                current_pos += 1


        instruction.stype(self, collected_lines)

        return len(instructions)

    def __str__(self: Self):
        return (f"Linear program. Current output values: {self.get_output_values()}\n") +\
                f"Constants c = {str(self.constants)},\n" +\
                f"Registers r = {str(self.registers)}"

    __repr__ = __str__

import random

A = LinearProgram(coarity = 3,
                  inputs = (1,2,3),
                  input_can_change = False,
                  reg_length = 4,
                  constants = (5,6,7),
                  initialiser = random.random)

initial_registers = list(A.registers.copy())

def add(a,b):
    return a + b

def sub(a,b):
    return a + b

def less(a,b):
    return a + b


oprs = [Operation(add, 1, (2, 3)),
        Operation(sub, 0, (1, 2)),
        Operation(add, 2, (-2, 2)),
        StructOverLines(If(Condition(less, (1, 2))), 2),
        Operation(add, 2, (-2, 2)),
        Operation(add, 2, (-3, 1)),
        ]

print("\n===== Running LGP in Context =====")
A.run(oprs)
print("\n===== End State of LGP =====")
print(str(A))

r = initial_registers
c = [5., 6., 7., 1., 2., 3.]
r[1] = add(r[2], r[3])
r[0] = sub(r[1], r[2])
r[2] = add(c[1], r[2])
if (1<2):
    r[2] = add(c[1], r[2])
    r[2] = add(c[2], r[1])


print("\n===== End State of Benchmark for Comparison =====")
print(f"Test: benchmark registers: {r},")
print(f"Benchmark constants: {c}")

