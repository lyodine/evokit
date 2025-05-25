"""This module 
"""

import importlib
from typing import Optional


def ensure_dependency(name: str,
                      package: Optional[str] = None) -> None:
    """

    :arg:`name` and :arg:`package` work the same as for
    :meth:`importlib.util.find_spec`.
    """
    if importlib.util.find_spec(name,  # type: ignore[attr-defined]
                                package) is None:
        raise ModuleNotFoundError(
            f"The dependency {f"{name}" if package is None
                              else f"{package}.{name}"}"
            "is not found. Please install it as an option.")
