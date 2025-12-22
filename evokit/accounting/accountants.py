from .watcher import Watcher
from ..evolvables.algorithms import HomogeneousAlgorithm
from ..core import Individual
from typing import Any

from typing import TypeVar

N = TypeVar("N", bound=float)


def fitness_watcher(events: list[str],
                       watch_automatic_events: bool = False)\
        -> Watcher[HomogeneousAlgorithm[Individual[Any]],
                      tuple[float, ...]]:
    """Return an :class:`Watcher` that collects the
    :attr:`.Individual.fitness` of the best individual in the
    population in the algorithm.

    Arg:
        events: Events that trigger the watcher.
        See :attr:`.Watcher.events`.

        watch_automatic_events: If ``True``, then automatic
        events also trigger the watcher. See :meth:`.Algorithm.step`
    """
    # "of the best individual in the population in the algorithm."
    # Certifiably, a mouthful.

    return Watcher(
        events=events,
        handler=lambda x: x.population.best().fitness,
        watch_automatic_events=watch_automatic_events
    )


def size_watcher(events: list[str],
                    watch_automatic_events: bool = False)\
        -> Watcher[HomogeneousAlgorithm[Any], int]:
    """Return an :class:`Watcher` that collects the
    length of the population in the algorithm.

    Arg:
        events: Events that trigger the watcher.
        See :attr:`.Watcher.events`.

        watch_automatic_events: If ``True``, then automatic
        events also trigger the watcher. See :meth:`.Algorithm.step`
    """
    return Watcher(
        events=events,
        handler=lambda x: len(x.population),
        watch_automatic_events=watch_automatic_events
    )
