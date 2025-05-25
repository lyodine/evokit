"""EvoKit uses no dependency, except when it does.

Some optional features such as visualisation may use
third-party packages. This module contains utilities to
check for dependencies.
"""

import importlib
from typing import Optional


def ensure_dependency(name: str,
                      package: Optional[str] = None,
                      option_name: Optional[str] = None) -> None:
    """Check if a dependency exists. If not, raise an error.

    Args:
        :arg:`name` and :arg:`package` work the same as for
        :meth:`importlib.util.find_spec`.

    Raise:
        ModuleNotFoundError: If the dependency does not exist.
        The message describes which dependency is missing and
        how it may be installed.
    """
    if importlib.util.find_spec(name,  # type: ignore[attr-defined]
                                package) is None:
        raise ModuleNotFoundError(
            f"The dependency {f"{name}" if package is None
                              else f"{package}.{name}"}"
            " is not found. Please install it as"
            f" {" an option." if option_name is None
                else f" evokit[{option_name}]."}"
        )
