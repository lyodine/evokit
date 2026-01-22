from typing import Sequence
from typing import Callable
from evokit.evolvables.lgp import Instruction
from evokit.evolvables.lgp import Operation
from evokit.evolvables.lgp import If
from evokit.evolvables.lgp import While
from evokit.evolvables.lgp import Condition
from evokit.evolvables.lgp import StructOverLines
from evokit.evolvables.lgp import StructUntilLabel
from evokit.evolvables.lgp import LinearProgram
from evokit.evolvables.lgp import StructNextLine
from evokit.evolvables.lgp import For
from evokit.evolvables.lgp import cells
from evokit.evolvables.lgp import Label


def add(a: float, b: float) -> float:
    return a + b


def sub(a: float, b: float) -> float:
    return a + b


def lt(a: float, b: float) -> bool:
    return a < b


def gt(a: float, b: float) -> bool:
    return a > b


def check_operation(verbose: bool) -> bool:
    """Text if simple arithmetic operations work.
    Also check if the program can be defined over other
    types (in this instance, a 2-tuple of floats).

    Initial state: ``r = ((0, 0),); c = ((-1, 1),)``

    Operations: repeat the following operation 3 times:

    .. code::
        r[0] := r[0] + c[0]

    Expected result: ``((-3, 3))``
    """
    def _add_tuple(a: tuple[float, float],
                   b: tuple[float, float]) -> tuple[float, float]:
        return (a[0] + b[0], a[1] + b[1])

    return run_and_check(
        [Operation(_add_tuple, 0, cells(0, -1)),
         Operation(_add_tuple, 0, cells(0, -1)),
         Operation(_add_tuple, 0, cells(0, -1)),],
        registers=[(0, 0)],
        constants=[(-1, 1)],
        end_state=[(-3, 3)],
        verbose=verbose
    )


def check_if_next_line(verbose: bool) -> bool:
    """Text if :class:`If` and :class:`StructNextLine` works.

    Initial state: ``r = (0,); c = (1, 2)``

    Operations:

    .. code::
        if r[0] < c[1]:
            r[0] = r[0] + c[0]
        if r[0] < c[1]:
            r[0] = r[0] + c[0]
        if r[0] < c[1]:
            r[0] = r[0] + c[0]

    Expected result: ``(2,)``
    """
    return run_and_check(
        [StructNextLine(If(Condition(lt, cells(0, -2)))),
         Operation(add, 0, cells(0, -1)),
         StructNextLine(If(Condition(lt, cells(0, -2)))),
         Operation(add, 0, cells(0, -1)),
         StructNextLine(If(Condition(lt, cells(0, -2)))),
         Operation(add, 0, cells(0, -1))],
        registers=[0],
        constants=(1, 2),
        end_state=[2],
        verbose=verbose
    )


def check_for_over_lines(verbose: bool) -> bool:
    """Text if :class:`For` and :class:`StructOverLines` works.

    Initial state: ``r = (0,); c = (1, 6, 5)``

    Operations:

    .. code::
        for (3 times):
            r[0] = r[0] + c[0]
            r[0] = r[0] + c[1]
        r[0] = r[0] + c[2]

    Expected result: ``(26,)``
    """

    return run_and_check(
        [StructOverLines(For(3), 2),
         Operation(add, 0, cells(0, -1)),
         Operation(add, 0, cells(0, -2)),
         Operation(add, 0, cells(0, -3)),],
        registers=[0],
        constants=[1, 6, 5],
        end_state=[26],
        verbose=verbose,
    )


def check_while_until_label(verbose: bool) -> bool:
    """Text if :class:`While` and :class:`StructUntilLabel` works.
    Also check if :class:`While` can take constants.

    Initial state: ``r = (0,); c = (3, 40, 7)``

    Operations:

    .. code::

        while True until l1:
            r[0] = r[0] + c[2] # Executes 20 times due to the cap
            while r[0] < c[1] until l2:
                r[0] = r[0] + c[0] # Happens 3 times so r[0]=39
        l1:

    Expected result: ``(173,)``
    """
    return run_and_check(
        [StructUntilLabel(While(True), "l1"),
         Operation(add, 0, cells(0, -3)),
         StructUntilLabel(While(Condition(lt, cells(0, -2))), "l2"),
         Operation(sub, 0, cells(0, -1)),
         Label("l2"),
         Label("l1"),],
        registers=[0],
        constants=[3, 40, 7],
        end_state=[173],
        verbose=verbose,
    )


def run_and_check[T](instructions: Sequence[Instruction[T]],
                     registers: Sequence[T],
                     constants: Sequence[T],
                     end_state: Sequence[T],
                     verbose: bool) -> bool:

    context = LinearProgram(
        constants=tuple(constants),
        registers=list(registers),
        verbose=verbose)

    context.run(instructions)

    return all(a == b for a, b in zip(context.registers,
                                      end_state))


TEST_SUITE: list[Callable[[bool], bool]] = [
    check_operation,
    check_if_next_line,
    check_for_over_lines,
    check_while_until_label
]


def check_all(verbose: bool = True) -> bool:
    return all(
        (test(verbose) for test in TEST_SUITE)
    )
