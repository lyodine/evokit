from __future__ import annotations

# It's just so appropriate here.
from abc import ABC
from typing import Annotated, Any, Sequence

import numpy as np

from abc import abstractmethod
from dataclasses import dataclass
from numbers import Number
from typing import Self, TypeVar, override

import random
from typing import List

from numpy import float64
from numpy.typing import NDArray

from typing import Callable, Tuple

T = TypeVar("T")


class Instruction():
    pass


class StructureType(ABC):
    """Base class for all structure scopes.

    Control structures consist of a :class:`.StructureType` and
    a :class:`.StructureScope`. The :class:`.StructureType` decides how
    the structure is executed: for example, whether it is an if statement
    (:class:`If`), a for loop (:class:`For`), or a while loop (:class:`While`).

    Derive this class to create custom structure scopes.
    """
    @abstractmethod
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        """Invoke instructions in the context of a linear program.

        Args:
            lgp: Context of execution.
            instructions: Instructions to execute.
        """


class StructureScope(ABC, Instruction):
    """Base class for all structure scopes.

    Control structures consist of a :class:`.StructureType` and
    a :class:`.StructureScope`. The :class:`.StructureScope` decides how
    many lines following the current line become part of the structure.

    Derive this class to create custom structure types.
    """
    @abstractmethod
    def __init__(self: Self,
                 stype: StructureType,
                 *args: Any,
                 **kwargs: Any) -> None:
        """
        Args:
            stype: Type of the control structure.
        """


class StructOverLines(StructureScope):
    """Control structure that spans multiple lines.
    """
    def __init__(self: Self, stype: StructureType, line_count: int) -> None:
        """
        Args:
            stype: Type of the control structure.
            line_count: Number of lines that the control structure spans.
        """
        self.stype: StructureType = stype
        self.line_count: int = line_count


class StructUntilLabel(StructureScope):
    """Control structure that extends to the given label.
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
    """Text label.

    Use with :class:`StructUntilLabel`.
    """
    def __init__(self: Self, label: str):
        """
        Args:
            label: Text of the label.
        """
        self.label = label


class For(StructureType):
    """Simple "for" loop.

    A control structure with this type repeats its body for
    :arg:`count` times.
    """
    def __init__(self: Self, count: int):
        self.count = count

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        for _ in range(self.count):
            lgp.run(instructions)


WHILE_LOOP_CAP = 20


class While(StructureType):
    """While loop.

    A control structure with this type repeats its body
    until :arg:`conditional` is satisfied.

    Warning:
        This control structure may execute indefinitely. To prevent
        this, the module constant ``.WHILE_LOOP_CAP`` imposes a bound
        to how many times a while loop may be repeated for.
    """
    def __init__(self: Self, conditional: Condition):
        """
        Arg:
            conditional: Condition that, if satisfied, ends the structures.
        """
        self.conditional = conditional

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        for _ in range(WHILE_LOOP_CAP):
            if (lgp.check(self.conditional)):
                lgp.run(instructions)
            else:
                break


class If(StructureType):
    """Structure with conditional execution.

    A control structure with this type executes once if :arg:`conditional`
    is satisfied. Otherwise, the structure is skipped and does nothing.
    """
    def __init__(self: Self, conditional: Condition):
        self.conditional = conditional

    @override
    def __call__(self: Self,
                 lgp: LinearProgram,
                 instructions: Sequence[Instruction]) -> None:
        if (lgp.check(self.conditional)):
            lgp.run(instructions)


@dataclass
class ValueRange:
    min: float
    max: float


@dataclass
class Operation(Instruction):
    """Algebraic operation.

    Call :arg:`function` with :arg:`args` as arguments.
    Assign the result to the register at position :arg:`target`.

    The argument :arg:`operands` can index constants and registers.
    Registers start at index 0; constants are represented as negative
    numbers starting at index -1. See :class:`.LinearProgram` for the
    source of this behaviour.
    """
    def __init__(self: Self,
                 function: Callable[..., float],
                 target: Annotated[int, ValueRange(0, float('inf'))],
                 operands: Tuple[int, ...]):
        """
        Args:
            function: Function to apply to :arg:`operands`.
            target: Register to deposit the result to.
            operands: Arguments to :arg:`function`.
        """
        self.function: Callable[..., float] = function
        self.target: int = target
        self.operands: Tuple[int, ...] = operands

        # If true, then operands are all constants. Apparently a bad thing
        #   according to the Banzhaf LGP book.
        # If this is the case, raise an warning.
        has_no_register_operand: bool = True

        for reg in operands:
            if reg >= 0:
                has_no_register_operand = False

        if (has_no_register_operand):
            raise ValueError("Operand registers are all constants")

    def __str__(self: Self) -> str:
        # Super Pythonic Code (R) (not really)
        args: str = ', '.join((f"r[{x}]" if x >= 0
                               else f"c[{-x - 1}]" for x in self.operands))
        function_name: str = getattr(self.function,
                                     '__name__',
                                     repr(self.function))

        return f"r[{self.target}] <- {function_name}({args})"

    __repr__ = __str__


class Condition():
    """Base class for predicates, or conditions.

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


class LinearProgram():
    """Context for executing linear programs.

    A :class:`LinearProgram` stores states (such as registers and constants) of
    the program.
    """
    def __init__(self: Self,
                 coarity: int,
                 inputs: Sequence[float],
                 input_can_change: bool,
                 reg_length: int,
                 constants: Sequence[float],
                 initialiser: float | Callable[[], float]):
        """
        Args:
            coarity: Size of the output vector.
            inputs: Input registers



        Note:
            :arg:`coarity`
        """

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
            current_line += self.run_instruction(instructions[current_line],
                                                 instructions,
                                                 current_line)

        return self.get_output_values()

    def get_output_values(self: Self) -> NDArray[np.float64]:
        """Return output registers.

        Return the values in the last :attr:`.coarity` registers.

        Note:
            If input registers are mutable, they are appended to the end of
            the registers. In that case, these registers are returned first.
        """
        return self.registers[:self.coarity]

    def check(self: Self, cond: Condition) -> bool:
        """Check if a condition is satisfied in the current context.
        """
        # Behold, Pythonic code!
        return cond.function(*(self.constants[-i - 1] if i < 0 else self.registers[i]
                             for i in cond.args))

    def run_instruction(self: Self, instruction: Instruction,
                        instructions: Sequence[Instruction],
                        pos: int) -> int:
        """Execute an instruction.

        Execute the instruction :arg:`instruction` in sequence
        :arg:`instructions` at position :arg:`pos`.

        Return the number of lines advanced as a result. Running a single operation
        advances the execution pointer by 1; running control structures may
        skip more lines.

        Arg:
            instruction: Instruction to run.
            instructions: Sequence of instruction to run :arg:`instruction` in.
            pos: Position of current execution pointer.

        """
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
                raise ValueError(f"Instruction type {type(instruction).__name__}"
                                 "Not recognised")

    def _run_label(self: Self) -> int:
        return 1

    def _run_operation(self: Self, instruction: Operation) -> int:
        if instruction.target < 0:
            raise ValueError("Malformed instruction: assignment to:"
                             f"c[{-instruction.target - 1}]")
        else:
            self.registers[instruction.target] =\
                instruction.function(
                    *(self.constants[-i - 1] if i < 0 else self.registers[i]
                      for i in instruction.operands))
        # print(str(instruction))
        return 1

    def _run_struct_over_lines(self: Self, instruction: StructOverLines,
                               instructions: Sequence[Instruction],
                               pos: int) -> int:
        collected_lines: List[Instruction] = []
        current_pos: int = pos + 1

        num_of_steps: int = min([len(instructions) - current_pos, instruction.line_count])

        for _ in range(num_of_steps - 1):
            print(f"Collect command into structure: {instructions[current_pos]}")
            collected_lines.append(instructions[current_pos])
            current_pos += 1

        instruction.stype(self, collected_lines)

        return num_of_steps

    def _run_struct_next_line(self: Self, instruction: StructNextLine,
                              instructions: Sequence[Instruction],
                              pos: int) -> int:

        collected_lines: List[Instruction] = []
        current_pos: int = pos + 1

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
        current_pos: int = pos + 1

        num_of_steps: int = len(instructions) - current_pos

        for _ in range(num_of_steps):
            current_instruction: Instruction = instructions[current_pos]

            if (isinstance(current_instruction, Label)
                    and current_instruction.label == instruction.label):
                current_pos += 1
                break
            else:
                collected_lines.append(instructions[current_pos])
                current_pos += 1

        instruction.stype(self, collected_lines)

        return len(instructions)

    def __str__(self: Self) -> str:
        return (f"Linear program. Current output values: {self.get_output_values()}\n"
                f"Constants c = {str(self.constants)},\n"
                f"Registers r = {str(self.registers)}")

    __repr__ = __str__


if __name__ == "__main__":
    A = LinearProgram(coarity=3,
                      inputs=(1, 2, 3),
                      input_can_change=False,
                      reg_length=4,
                      constants=(5, 6, 7),
                      initialiser=random.random)

    initial_registers = list(A.registers.copy())

    def add(a: float, b: float) -> float:
        return a + b

    def sub(a: float, b: float) -> float:
        return a + b

    def less(a: float, b: float) -> bool:
        return a < b

    oprs: Sequence[Instruction] = [Operation(add, 1, (2, 3)),
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

    if (1 < 2):
        r[2] = add(c[1], r[2])
        r[2] = add(c[2], r[1])

    print("\n===== End State of Benchmark for Comparison =====")
    print(f"Test: benchmark registers: {r},")
    print(f"Benchmark constants: {c}")
