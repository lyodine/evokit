from typing import Callable
from dataclasses import dataclass
#: Type for an endofunction.
type Endofunction[R] = Callable[..., R]
# Note that this is a very weak specification. It does not
#   say what the `Callable` should take, only that
#   it needs to return an `R`.
# The next best is `Concatenate[R, ...]`.
# Technically this type means functions that take
#   one R as argument as minimum -- it doesn't care what
#   arguments come next.
# This is because to my knowledge, Python has no facility
#   for this -- typing it variadic would preclude,
#   for example, functions such ``add(a, b)`` that
#   are not variadic. Some features are "left to future PEPs";
#   I suspect what I want is among those.

#: Type of a boolean-valued function.
type Predicate[R] = Callable[..., bool]
# For the same reason as :class:`.Endofunction`, there does
#   not appear to be a way to correctly type this thing.


#: Used for hinting the range of a type.
#: Example: ``Annotated[float, ValueRang(0, 1)]``.
@dataclass
class ValueRange:
    """Represents a range of numbers.
    """
    min: float
    max: float
# This practice seems common at the time of this commit.
# If a better approach comes up, replace this.
