from ..watch import Watcher
from ..watch.watcher import C
from .._utils.dependency import ensure_installed
from ..evolvables.algorithms import Algorithm

import psutil
from enum import Enum, auto
from typing import Optional
from typing import Generator

import tracemalloc

from collections.abc import Container, Iterable
from typing import Callable, Self
from typing import override

ensure_installed("guppy")
from guppy.heapy.UniSet import IdentitySet
from guppy import hpy

ensure_installed("pympler")
import pympler.asizeof

#: Recursion limit of ``pympler.asizeof.asizeof``.
PYMPLER_ASIZEOF_RECURSION_LIMIT: int = 5


class MemoryWatcherMetric(Enum):
    """Metrics that can be measured by
    :class:`.MemoryWatcher`.
    """
    psutil_rss = auto()
    psutil_vms = auto()
    psutil_rss_plus_children = auto()
    psutil_vms_plus_children = auto()
    pympler_asizeof_algorithm = auto()
    guppy3_domisize_algorithm = auto()
    tracemalloc_total_current = auto()
    tracemalloc_total_peak = auto()
    tracemalloc_snapshot = auto()


class MemoryWatcher(Watcher[C,
                            dict[MemoryWatcherMetric,
                                 int
                                 | tracemalloc.Snapshot]]):
    """A highly evolved :class:`Watcher` with
    the ability to explore entire memory footprints.
    Returns a

    Memory profiling is tricky. For example, the
    :mod:`tracemalloc` module is only able to track memory
    allocations made inside the Python iterator and therefore
    does not work well with PyTorch tensors, NumPy arrays, and
    Cython modules.

    To remedy this, this watcher supports several metrics
    (see :attr:`.MemoryWatcher.Metric`). Only those
    given to :meth:`MemoryWatcher.__init__` will
    be measured and reported.

    Also note that, because this watcher is attached to
    an algorithm, it is also part of the algorithm's
    memory footprint.
    """

    supported_metrics: set[MemoryWatcherMetric] = \
        set(MemoryWatcherMetric)

    #: Maps each
    metric_to_measure: dict[MemoryWatcherMetric,
                            Callable[[Algorithm,
                                      'MemoryWatcher'],
                                     int
                                     | tuple[int, int]
                                     | tracemalloc.Snapshot]] = {

        MemoryWatcherMetric.psutil_rss: lambda _, __:
            psutil.Process().memory_info().rss,
        MemoryWatcherMetric.psutil_vms: lambda _, __:
            psutil.Process().memory_info().vms,
        MemoryWatcherMetric.psutil_rss_plus_children:
            lambda _, __: psutil.Process().memory_info().rss
            + sum(x.memory_info().rss for x in psutil.Process().children()),
        MemoryWatcherMetric.psutil_vms_plus_children:
            lambda _, __: psutil.Process().memory_info().vms
            + sum(x.memory_info().vms for x in psutil.Process().children()),
        MemoryWatcherMetric.pympler_asizeof_algorithm: lambda _algo, __:
            pympler.asizeof.asizeof(_algo,
                                    limit=PYMPLER_ASIZEOF_RECURSION_LIMIT),
        MemoryWatcherMetric.guppy3_domisize_algorithm: lambda _, _wat:
            _wat._isoset_algo.domisize
            if _wat._isoset_algo is not None else -1,  # type: ignore
        MemoryWatcherMetric.tracemalloc_total_current:
            lambda _, __: tracemalloc.get_traced_memory()[0],
            MemoryWatcherMetric.tracemalloc_total_peak:
            lambda _, __: tracemalloc.get_traced_memory()[0],
        MemoryWatcherMetric.tracemalloc_snapshot:
            lambda _, __: tracemalloc.take_snapshot(),
    }

    def __init__(self: Self,
                 events: Container[str],
                 metrics: Iterable[MemoryWatcherMetric],
                 stride: int = 1,
                 watch_post_step: bool = False):
        """
        Args:
            events: See :class:`.Watcher`.

            metrics: Metrics to measure and report.

            handler: See :class:`.Watcher`.

            stride: See :class:`.Watcher`.

            watch_automatic_events: See :class:`.Watcher`.

        Effect:
            Cause :mod:`tracemalloc` to start tracing memory allocations.
            Call :meth:`MemoryWatcher.close` to stop.

        """
        """A collection of Guppy3 :class:`IsoSet`\\ s.
        Initialised by :meth:`subscribe`.
        """
        self._isoset_algo: Optional[IdentitySet] = None

        #: Metrics that are measured and reported by this watcher.
        self.metrics: Iterable[MemoryWatcherMetric] = metrics
        tracemalloc.start()

        def _meme(algo: C) -> dict[MemoryWatcherMetric,
                                   int
                                   | tracemalloc.Snapshot]:
            result = {}
            for kr in metrics:
                result[kr] = self.metric_to_measure[kr](algo, self)

            return result

        super().__init__(events=events,
                         handler=_meme,
                         stride=stride,
                         watch_post_step=watch_post_step)

    @override
    def subscribe(self: Self, subject: C) -> None:
        super().subscribe(subject)

        if MemoryWatcherMetric.guppy3_domisize_algorithm in self.metrics:
            self._isoset_algo = hpy().iso(subject)

    def close(self: Self):
        """Stop tracemalloc from tracing memory allocation.
        """
        tracemalloc.start()


class AttributeMemoryWatcher(Watcher[C, dict[str, int]]):
    """A :class:`.MemoryWatcher` that inspects
    select attributes.

    The initialiser accepts a list of attribute names.
    For each name, that attribute of the :attr:`.Watcher.subject`
    is measured with ``asizeof`` (from Pympler) and
    ``IdentitySet.domisize`` (from Guppy3).
    """

    def __init__(self: Self,
                 events: Container[str],
                 attributes: Iterable[str],
                 stride: int = 1,
                 watch_post_step: bool = False):
        """
        Args:
            events: See :class:`.Watcher`.

            attributes: Names of attributes to measure and report.

            handler: See :class:`.Watcher`.

            stride: See :class:`.Watcher`.

            watch_automatic_events: See :class:`.Watcher`.

        """
        #: Names of attributes to watch.
        self.attributes = attributes

        """A collection of Guppy3 :class:`IsoSet`\\ s.
        Initialised by :meth:`subscribe`.
        """
        self._isosets: dict[str, IdentitySet] = {}

        def _lud(algo: C) -> dict[str, int]:
            # Do not comment. The type hint is more than
            #   self-explanatory.
            def _yield_stuff(algo: C, attributes: Iterable[str])\
                    -> Generator[tuple[str, int], None, None]:
                for attr in attributes:
                    yield (f"guppy_domisize_{attr}",
                           self._isosets[attr].domisize)  # type: ignore
                    yield (f"pumpler_asizeof_{attr}",
                           pympler.asizeof.asizeof(
                               getattr(self.subject, attr),
                               limit=PYMPLER_ASIZEOF_RECURSION_LIMIT))

            return dict(tuple(_yield_stuff(algo, attributes)))

        super().__init__(events=events,
                         handler=_lud,
                         stride=stride,
                         watch_post_step=watch_post_step)

    @override
    def subscribe(self: Self, subject: C) -> None:
        for attr in self.attributes:
            assert hasattr(subject, attr)

        super().subscribe(subject)

        for attr in self.attributes:
            self._isosets[attr] = hpy().iso(getattr(subject, attr))
