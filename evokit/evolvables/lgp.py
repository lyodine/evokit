from __future__ import annotations
import numpy as np

from typing import Annotated, Sequence

# It's just so appropriate here.
import numpy
from abc import ABC

from functools import singledispatch
class Instruction():
    pass


from abc import abstractmethod

from dataclasses import dataclass

from typing import override


class Runner(ABC):
    @abstractmethod
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        pass

class StructOverLines(ABC):
    def __init__(self: Self, runner: Runner, line_count: int):
        self.runner: Runner = runner
        self.line_count: int = line_count

class StructUntilLabel(ABC):
    def __init__(self: Self, runner: Runner, label: str):
        self.runner: Runner = runner
        self.label: str = label

class StructNextLine(ABC):
    def __init__(self: Self, runner: Runner):
        self.runner: Runner = runner

class Label():
    def __init__(self: Self, label: str):
        self.label = label

class For(Runner):
    def __init__(self: Self, count: int):
        self.count = count

    @override
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        for _ in range(self.count):
            lgp.run(instructions)

WHILE_LOOP_CAP = 20

class While(Runner):
    def __init__(self: Self, conditional: Conditional):
        self.conditional = conditional

    @override
    def __call__(self, lgp: LinearProgram, instructions: Sequence[Instruction]):
        for _ in range(WHILE_LOOP_CAP):
            if (lgp.check(self.conditional)):
                lgp.run(instructions)
            else:
                break

class If(Runner):
    def __init__(self: Self, conditional: Conditional):
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
    def __init__(self: Self,
                 function: Callable[..., float],
                 target: Annotated[int, ValueRange(0, float('inf'))],
                 args: Tuple[int, ...]):
        
        #: Function of the operation.
        self.function: Callable[..., float] = function

        #: Index of the target register.
        self.target: int = target
        
        has_no_register_operand: bool = True
        for reg in args:
            if reg >= 0:
                has_no_register_operand = False

        if (has_no_register_operand):
            raise ValueError(f"Operand registers are all constants")
        #: Indices of operand registers
        self.args: Tuple[int, ...] = args

    def __str__(self: Self):
        args: str = ', '.join((f"r[{x}]" if x >= 0 else f"c[{-x-1}]" for x in self.args))
        function_name: str = getattr(self.function,
                                     '__name__',
                                     repr(self.function))
        
        return f"r[{self.target}] <- {function_name}({args})"
    
    __repr__ = __str__

class Conditional():
    def __init__(self: Self,
                 function: Callable[..., bool],
                 args: Tuple[int, ...]):
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

        print(f"pos is frs{current_pos}")
        
        for _ in range(num_of_steps):
            print(f"sasss frs{instructions[current_pos]}")
            collected_lines.append(instructions[current_pos])
            current_pos += 1

        print(f"pos is {current_pos}")
        print(f"collected {collected_lines}")

        instruction.runner(self, collected_lines)

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
        instruction.runner(self, collected_lines)
        

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


        instruction.runner(self, collected_lines)

        return len(instructions)
        
    def __str__(self: Self):
        return (f"Linear program. Current output values: {self.get_output_values()}\n") +\
                f"Constants c = {str(self.constants)}" +\
                f"Registers r = {str(self.registers)}"

    __repr__ = __str__

import random

A = LinearProgram(coarity = 3,
                  inputs = (1,2,3),
                  input_can_change = False,
                  reg_length = 4,
                  constants = (5,6,7),
                  initialiser = random.random)

def add(a,b):
    return a + b

def sub(a,b):
    return a + b

def less(a,b):
    return a + b

oprs = [Operation(add, 1, (2, 3)),
        Operation(sub, 0, (1, 2)),
        Operation(add, 2, (-2, 2)),
        StructOverLines(If(Conditional(less, (1, 2))), 2),
        Operation(add, 2, (-2, 2)),
        Operation(add, 2, (-3, 1)),
        ]

A.run(oprs)
print(str(A))


