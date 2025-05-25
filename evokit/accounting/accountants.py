from .accountant import Accountant
from ..evolvables.algorithms import HomogeneousAlgorithm
from ..core import Individual
from typing import Any

from typing import TypeVar

N = TypeVar("N", bound=float)


def fitness_accountant(events: list[str],
                       watch_automatic_events: bool = False)\
        -> Accountant[HomogeneousAlgorithm[Individual[Any]],
                      tuple[float, ...]]:
    """Return an :class:`Accountant` that collects the
    :attr:`.Individual.fitness` of the best individual in the
    population in the algorithm.

    Arg:
        events: Events that trigger the accountant.
        See :attr:`.Accountant.events`.

        watch_automatic_events: If ``True``, then automatic
        events also trigger the accountant. See :meth:`.Algorithm.step`
    """
    # "of the best individual in the population in the algorithm."
    # Certifiably, a mouthful.

    return Accountant(
        events=events,
        handler=lambda x: x.population.best().fitness,
        watch_automatic_events=watch_automatic_events
    )


def size_accountant(events: list[str],
                    watch_automatic_events: bool = False)\
        -> Accountant[HomogeneousAlgorithm[Any], int]:
    """Return an :class:`Accountant` that collects the
    length of the population in the algorithm.

    Arg:
        events: Events that trigger the accountant.
        See :attr:`.Accountant.events`.

        watch_automatic_events: If ``True``, then automatic
        events also trigger the accountant. See :meth:`.Algorithm.step`
    """
    return Accountant(
        events=events,
        handler=lambda x: len(x.population),
        watch_automatic_events=watch_automatic_events
    )
