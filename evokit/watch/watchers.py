from .watcher import Watcher
from ..evolvables.algorithms import HomogeneousAlgorithm
from ..core import Individual
from typing import Any
from typing import Callable
import time
import psutil

from typing import TypeVar

N = TypeVar("N", bound=float)


def create_fitness_watcher(events: list[str],
                           stride: int = 1,
                           *,
                           watch_post_step: bool = False,
                           timer: Callable[[], float] = time.process_time)\
        -> Watcher[HomogeneousAlgorithm[Individual[Any]],
                   tuple[float, ...]]:
    """Return an :class:`Watcher` that collects the
    best :attr:`.Individual.fitness` of a
    :attr:`HomogeneousAlgorithm.population`.

    See :meth:`Watcher.__init__` for parameters.
    """

    return Watcher(
        events=events,
        stride=stride,
        handler=lambda x: x.population.best().fitness,
        watch_post_step=watch_post_step,
        timer=timer
    )


def create_size_watcher(events: list[str],
                        stride: int = 1,
                        *,
                        watch_post_step: bool = False,
                        timer: Callable[[], float] = time.process_time)\
        -> Watcher[HomogeneousAlgorithm[Individual[Any]],
                   int]:
    """Return an :class:`Watcher` that collects the
    size of the population.

    See :meth:`Watcher.__init__` for parameters.
    """

    return Watcher(
        events=events,
        stride=stride,
        handler=lambda x: len(x.population),
        watch_post_step=watch_post_step,
        timer=timer
    )


def create_cpu_watcher(events: list[str],
                       stride: int = 1,
                       *,
                       watch_post_step: bool = False,
                       timer: Callable[[], float] = time.process_time)\
        -> Watcher[HomogeneousAlgorithm[Individual[Any]],
                   float]:
    """Return an :class:`Watcher` that collects the
    CPU time of the process.

    See :meth:`Watcher.__init__` for parameters.
    """

    return Watcher(
        events=events,
        stride=stride,
        handler=lambda _: psutil.Process().cpu_percent(),
        watch_post_step=watch_post_step,
        timer=timer
    )


def create_rss_watcher(events: list[str],
                       stride: int = 1,
                       *,
                       watch_post_step: bool = False,
                       timer: Callable[[], float] = time.process_time)\
        -> Watcher[HomogeneousAlgorithm[Individual[Any]],
                   float]:
    """Return an :class:`Watcher` that collects the
    memory usage (RSS) of an algorithm.

    See :meth:`Watcher.__init__` for parameters.
    """
    # "of the best individual in the population in the algorithm."
    # Certifiably, a mouthful.

    return Watcher(
        events=events,
        stride=stride,
        handler=lambda _: psutil.Process().memory_info().rss,
        watch_post_step=watch_post_step,
        timer=timer
    )
