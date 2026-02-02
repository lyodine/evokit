from typing import Protocol
import math
from typing import TypeVar


class Comparable(Protocol):
    def __lt__(self, other) -> bool:
        ...

    def __gt__(self, other) -> bool:
        ...

    def __eq__(self, other) -> bool:
        ...


R = TypeVar("R", bound=Comparable)


def gt(a: R, b: R) -> bool:
    return a > b


def lt(a: R, b: R) -> bool:
    return a < b


def geq(a: R, b: R) -> bool:
    return not a < b


def leq(a: R, b: R) -> bool:
    return not a > b


def eq(a: R, b: R) -> bool:
    try:
        # Suppressing typing errors because it's in a try
        #   block. If something goes wrong, we go except.
        return math.isclose(a, b)  # type: ignore
    except TypeError:
        return a == b


def neq(a: R, b: R) -> bool:
    return not eq(a, b)
