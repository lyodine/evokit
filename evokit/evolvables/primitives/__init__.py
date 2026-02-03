"""This module contains arithmetic and logical primitives.
These are used for genetic programming

Arithmetic primitives in this module are protected. Primitives
in this module may be recognised by the optimiser.
"""

from ._arithmetic import sin, cos, add, sub, mul, div, avg, lim
from ._logical import gt, lt, geq, leq, eq, neq

__all__ = [
    "sin", "cos", "add", "sub", "mul", "div", "avg", "lim",
    "gt", "lt", "geq", "leq", "eq", "neq"
]
