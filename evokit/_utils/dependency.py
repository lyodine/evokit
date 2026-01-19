"""EvoKit uses no dependency, except when it does.

Some optional features such as visualisation may use
third-party packages. This module contains utilities to
check for dependencies.
"""

import importlib
import importlib.util
from importlib.metadata import metadata
from importlib.metadata import PackageNotFoundError

from packaging.requirements import Requirement

# Fetch dependency information from package.

type Name = str
type Extra = str
type RequirementText = str

"""A dictionary of form {package_name: dependency_name}.
Ignores ``full`` and ``all``.
"""
optional_dependencies: dict[Name,
                            Extra] = {}

try:
    evokit_metadata = metadata("evokit")
    od_metadata = metadata("evokit").get_all("Requires-Dist")
    if od_metadata is not None:
        for each in od_metadata:
            # Each string follows the form
            #   '<name>??<version>; extra == <option_name>'
            each_split: str = each.split("; ")
            name: str = Requirement(each_split[0]).name
            extra: str = each_split[1].split("extra == ")[1].strip("\"")
            if extra != "full" and extra != "all":
                optional_dependencies[name] = extra

except PackageNotFoundError:
    print("EvoKit is not installed ... how?"
          " For some reason, a package named"
          " `evokit` is not found, while this function"
          " is part of `evokit`."
          " The only explanation I can think of"
          " is that you're running it with another name."
          " Please contact the developer if this happens,"
          " because I can't think of how it would even"
          " be possible.")


def is_installed(name: str) -> bool:
    return importlib.util.find_spec(
        name) is not None  # type: ignore[attr-defined]


def query_option(name: str) -> str:
    """Machinery.

    :meta private:

    Args:
        :arg:`name` works the same as for
        :meth:`importlib.util.find_spec`.

    Raise:
        ModuleNotFoundError: If the dependency does not exist,
        of if the dependency is not listed as an option by
        EvoKit.
    """
    if name not in optional_dependencies:
        raise ModuleNotFoundError(f"The required package {name} is"
                                  " not listed as an optional"
                                  " dependency of EvoKit. This is"
                                  " likely a developer error.")
    else:
        return optional_dependencies[name]


def ensure_installed(name: str) -> None:
    """Check if a dependency exists. If not, raise an error.
    Otherwise, do nothing.

    Args:
        :arg:`name` works the same as for
        :meth:`importlib.util.find_spec`.

    Raise:
        ModuleNotFoundError: If the dependency does not exist.
    """
    option: str = query_option(name)

    if not is_installed(name):
        raise ModuleNotFoundError(
            f"The dependency {f"{name}"} is"
            " not found. Please install it as"
            f" evokit[{option}]."
        )


# def import_if_installed(name: str) -> None:
#     """Check if a dependency exists. If yes, import it.
#     do nothing.

#     Args:
#         :arg:`name` and :arg:`package` work the same as for
#         :meth:`importlib.util.find_spec`.

#     Raise:
#         ModuleNotFoundError: If the dependency does not exist.
#         The message describes which dependency is missing and
#         how it may be installed.
#     """
#     _ensure_is_option(name)

#     if importlib.util.find_spec(name,  # type: ignore[attr-defined]
#                                 ) is not None:
#         importlib.import_module(name)
