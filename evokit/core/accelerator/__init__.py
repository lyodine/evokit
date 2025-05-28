"""This module contains utility functions
that parallelise the standard :class:`Variator`
and the standard :class:`Evaluator`.

Module name is coincidentally French.
"""
from .parallelisers import parallelise_task

__all__ = ["parallelise_task",]
