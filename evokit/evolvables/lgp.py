# flake8: noqa 
# type: ignore

from __future__ import annotations

# It's just so appropriate here.
from abc import ABC
from typing import Annotated, Any, Sequence

import numpy as np

from abc import abstractmethod
from dataclasses import dataclass
from typing import Self, TypeVar, override
from typing import Iterable
from typing import Callable

from numpy import float64
from numpy.typing import NDArray

from typing import TypeAlias
from enum import Enum, auto

from .._utils.addons import ensure_dependency

ensure_dependency("numpy", None)

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


class While(StructureType):
    """While loop.

    A control structure with this type repeats its body
    until :arg:`conditional` is satisfied.

    Warning:
        This control structure may execute indefinitely. To prevent
        this, the class variable :attr:`.loop_cap` imposes a bound
        to how many times a while loop may be repeated for.
    """

    #: Maximum number of iterations a :class:`While` loop can run for.
    loop_cap = 20

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
        for _ in range(While.loop_cap):
            if (lgp.check_condition(self.conditional)):
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
        if (lgp.check_condition(self.conditional)):
            lgp.run(instructions)


# TODO fix doc
@dataclass
class ValueRange:
    min: float
    max: float


class StateVectorType(Enum):
    """Type of a state vector.

    A linear program stores three state vectors:
    the input vector :attr:`.LinearProgram.inputs`,
    the mutable register :attr:`.LinearProgram.registers`, and
    the constant register :attr:`.LinearProgram.constants`,
    """
    input = auto()
    register = auto()
    constant = auto()


#: Tuple that locates an item in a state vector.
#: The first item (:class:`StateVectorType`) specifies the state vector, then
#:      the second item (:class:`int`) gives the index.
CellSpecifier: TypeAlias = tuple[StateVectorType,
                                 Annotated[int, ValueRange(0, float('inf'))]]


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
                 target: int,
                 operands: tuple[CellSpecifier, ...]):
        """
        Args:
            function: Function to apply to :arg:`operands`.
            target: Register to deposit the result to.
            operands: Arguments to :arg:`function`.
        """
        self.function: Callable[..., float] = function
        self.target: int = target
        self.operands: tuple[CellSpecifier, ...] = operands

        # Check if all operands are constants. A bad thing
        #   according to the B&B LGP book.
        # Do not, however, check if the target is a register, because
        #   :attr:`.inputs` and :attr:`.constants` are already immutable.
        has_register_operand: bool
        has_register_operand = any(opr[0] == StateVectorType.register
                                   for opr in operands)

        if not has_register_operand:
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
                 args: tuple[int, ...]):
        """
        Args:
            function: TODO
            args: TODO
        """
        self.function = function
        self.args = args


class LinearProgram():
    """Context for executing linear programs.

    A :class:`LinearProgram` stores states (such as registers and constants) of
    the program.
    """
    def __init__(self: Self,
                 registers: Iterable[float],
                 constants: Iterable[float],
                 inputs: Iterable[float],):
        """
        Args:
            coarity: Size of the output vector, taken from the end of the register vector.
            inputs: Input registers.
            input_can_change: If `True`, then append :arg:`inputs` to the register
                vector. Otherwise, append :arg:`inputs` to the constant vector.
            initialiser: Initialiser for the register vector. Can be one of:
                * a number, which populates each register;
                * a sequence of numbers, which is converted to the register; or
                * a nullary function, whose return value populates each register.
            reg_length: Length of the register vector. If :arg:`initialiser` is
                a sequence, then its length must match :arg:`s`.
            constants: The constant vector.

        Note:
            Both constants and registers are indexed by integers.

            * Indices for registers begin at 0. Examples: 0, 1, 2, ...

            * Indices for constants begin at -1. Examples: -1, -2, -3, ...
        """
        #: The register vector stores mutable state variables.
        #: Set with :meth:`.set_register`.
        self.registers: NDArray[np.float64]
        self.set_registers(registers)

        #: The constant vector stores immutable state variables.
        #: Set with :meth:`.set_constants`.
        self.constants: NDArray[np.float64]
        self.set_constants(constants)

        #: The input vector stores immutable input variables.
        #: Unlike constants, inputs may change each time the program is called.
        #: Set with :meth:`.set_inputs`.
        self.set_inputs(inputs)

        # Where is the mutable state variable? (xiao

    def set_registers(self: Self, registers: Iterable[float]) -> None:
        """Update the register vector with :arg:`registers`.
        """
        self.registers = np.fromiter(registers, dtype=float64)

    def set_constants(self: Self, constants: Iterable[float]) -> None:
        """Update the constant vector with :arg:`constants`.
        """
        self.constants = np.fromiter(constants, dtype=float64)
        self.constants.flags.writeable = False

    def set_inputs(self: Self, inputs: Iterable[float]) -> None:
        """Update the input vector with :arg:`inputs`.
        """
        self.inputs = np.fromiter(inputs, dtype=float64)
        self.inputs.flags.writeable = False

    def get_state_vector(self: Self, celltype: StateVectorType) -> NDArray[np.float64]:
        """Return the state vector specified by :arg:`cellspec`.
        """
        match celltype:
            case StateVectorType.input:
                return self.inputs
            case StateVectorType.register:
                return self.registers
            case StateVectorType.constant:
                return self.constants
            case _:
                raise ValueError("Cell specifier fails to locate a vector."
                                 f"Expected: a `CellType`; got: {celltype}")

    def run(self: Self, instructions: Sequence[Instruction]) -> None:
        """Execute :arg:`instructions` in this context.

        Effect:
            Instructions, for example :class:`Operation` s, may alter
            the state of this context.
        """
        current_line: int = 0

        while current_line < len(instructions):
            current_line += self.run_instruction(instructions[current_line],
                                                 instructions,
                                                 current_line)

    def check_condition(self: Self, cond: Condition) -> bool:
        """Check if :arg:`cond` is satisfied in the current context.
        """
        # Behold, Pythonic code!
        # TODO rewrite logic
        return cond.function(*(self.constants[-i - 1] if i < 0 else self.registers[i]
                             for i in cond.args))

    def run_instruction(self: Self, instruction: Instruction,
                        instructions: Sequence[Instruction],
                        pos: int) -> int:

        # Let's check - is it always the case that instructions[pos] is instruction?
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

        # TODO rewrite logic
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
        collected_lines: list[Instruction] = []
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

        collected_lines: list[Instruction] = []
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

        collected_lines: list[Instruction] = []
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
        return (f"This is a linear program."
                f"Constants c = {str(self.constants)},\n"
                f"Registers r = {str(self.registers)}")

    __repr__ = __str__
