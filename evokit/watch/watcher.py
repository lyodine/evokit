from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Generic
from ..core.algorithm import Algorithm
from typing import TypeVar
from typing import override, overload
from dataclasses import dataclass
from dataclasses import field

import time

if TYPE_CHECKING:
    from typing import Self
    from typing import Callable
    from typing import Optional
    from collections.abc import Container

from typing import Sequence
C = TypeVar("C", bound=Algorithm)

T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class WatcherRecord(Generic[T]):
    """A record collected by an :class:`Watcher` from an :class:`Algorithm`.
    Also records the generation count and time of collection.
    """
    # TODO Sphinx somehow collects `__new__`, which should not be documented.
    # Spent 1 hour on this to no avail, will leave it be for the interest
    #   of time.

    #: Event that triggered the handler.
    event: str

    #: Generation count when the event :attr:`event` occurs.
    generation: int

    #: Data collected in :attr:`generation` after :attr:`event`.
    value: T

    #: Time (by :meth:`time.process_time`) when the event :attr:`event` occurs.
    time: float = field(default_factory=time.process_time)


class Watcher(Generic[C, T], Sequence[WatcherRecord[T]]):
    """Observes and collect data from a running :class:`Algorithm`.

    The :class:`Watcher` should be registered to an
    :class:`Algorithm`, which then becomes the watcher's
    :attr:`subject`. When an event fires in the subject,
    if that event is in the watcher's :attr:`events`,
    then the :attr:`handler` will be called with the subject as argument.
    Results are collected as a sequence of :class:`WatcherRecord`\\ s.

    Call :meth:`.Algorithm.register` to register an :class:`Watcher` to
    a :class:`Algorithm`. Call :meth:`report` to retrieve collected records.

    For type checking purposes, the :class:`Watcher` has two
    type parameter ``C`` and ``T``. ``C`` is the type of the observed
    :class:`Algorithm`; ``T`` is the type of `.value` in the reported
    :class:`WatcherRecord`.

    Tutorial: :doc:`../guides/examples/watcher`.
    """

    MANUAL_EVENT: str = "MANUAL_TRIGGER"

    def __init__(self: Self,
                 events: Container[str],
                 handler: Callable[[C], T],
                 stride: int = 1,
                 *,
                 watch_post_step: bool = False):
        """
        Args:
            events: Events that trigger the :arg:`handler`.

            handler: Callable that takes the attached algorithm as input.

            stride: Collection interval. Only :arg:`stride` :sup:`th`
                event triggers :attr:`handler`.

            watch_post_step: If ``True``, also watch the ``POST_STEP``
                event. This event fires automatically after
                :meth:`Algorithm.step`.
        """
        #: Records collected by the :class:`Watcher`.
        self._records: list[WatcherRecord[T]] = []

        self.events: Container[str] = events

        self.handler: Callable[[C], T] = handler

        #: The attached :class:`Algorithm`.
        self.subject: Optional[C] = None

        self.watch_post_step = watch_post_step

        self._passed_since_last_update = 0

        self.stride = stride

    def subscribe(self: Self, subject: C) -> None:
        """Machinery.

        :meta private:

        Subscribe for events in a :class:`.Algorithm`.

        Args:
            subject: the :class:`.Algorithm` whose events are seen by
                this watcher.
        """
        self.subject = subject

    def update(self: Self, event: str) -> None:
        """When the :attr:`subject` calls :meth:`.Algorithm.update`,
        the subject calls this method on every watcher registered to it.

        When an event matches a key in :attr:`handlers`, call the
        corresponding value with the subject as argument. Store the
        result in :attr:`records`.

        To trigger collections, call :meth:`manual_update` instead
        of this method.

        Raise:
            RuntimeError: If no :class:`Algorithm` is attached.
        """
        if event in self.events\
                or (self.watch_post_step
                    and (event == "POST_STEP")):
            self._passed_since_last_update += 1
            if self._passed_since_last_update >= self.stride:
                self.force_update(event)
                self._passed_since_last_update = 0

    def force_update(self: Self,
                     event: str = "MANUAL_EVENT") -> None:
        """Manually trigger :meth:`update`, bypassing all checks of
        whether event is observed.

        Args:
            event: Name of an event. Defaults to ``MANUAL_EVENT``.

        Raise:
            RuntimeError: If no :class:`Algorithm` is attached.
        """
        if self.subject is None:
            raise RuntimeError("Watcher updated without a subject.")
        else:
            self._records.append(
                WatcherRecord(event,
                              self.subject.generation,
                              self.handler(self.subject)))

    def report(self: Self) -> list[WatcherRecord[T]]:
        """Report collected records.
        """
        return self._records

    def is_registered(self: Self) -> bool:
        """Return if this watcher is observing an :class:`.Algorithm`.
        """
        return self.subject is not None

    def purge(self: Self) -> None:
        """Remove all collected records.

        Effect:
            Reset collected records to an empty list.
        """
        self._records = []

    @override
    def __len__(self: Self) -> int:
        return len(self._records)

    @overload
    def __getitem__(self: Self,
                    index: int) -> WatcherRecord[T]:
        pass

    @overload
    def __getitem__(self: Self,
                    index: slice) -> Sequence[WatcherRecord[T]]:
        pass

    @override
    def __getitem__(self: Self,
                    index: int | slice)\
            -> WatcherRecord[T] | Sequence[WatcherRecord[T]]:
        return self._records[index]
