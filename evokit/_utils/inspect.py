from inspect import signature

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from typing import Callable


def get_default_value(func: Callable,
                      parameter_name: str)\
        -> Any:
    """Inspect and return the default value of
    ``callable.parameter_name``.

    If no such default value is found (whether :arg:`callable`
    does not have a parameter by name :arg:`parameter_name`) or
    :arg:`parameter_name` does not have a default value, raise
    an exception.

    Args:
        func: A :class:`Callable` to inspect.

        parameter_name: Name of a parameter in :arg:`func`\\ 's signature.

    Raise:
        ValueError: If no default value is found.
    """
    default_val_list =\
        [para.default
         for para in signature(func).parameters.values()
         if para.name == parameter_name
         and para.default is not para.empty]

    if len(default_val_list) < 1:
        raise ValueError("No default value found for"
                         f" {func.__name__}.{parameter_name}.")

    if len(default_val_list) > 1:
        raise ValueError("Somehow ")

    return default_val_list
