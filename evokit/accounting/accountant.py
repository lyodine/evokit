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
class AccountantRecord(Generic[T]):
    """A record collected by an :class:`Accountant` from an :class:`Algorithm`.
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

    #: Time (by :meth:`time.perf_counter`) when the event :attr:`event` occurs.
    time: float = field(default_factory=time.perf_counter)


class Accountant(Generic[C, T], Sequence[AccountantRecord[T]]):
    """Monitor and collect data from a running :class:`Algorithm`.

    The :class:`Accountant` should be registered to an
    :class:`Algorithm`. Then, when an event fires in the algorithm,
    if that event is in :attr:`events`, then :attr:`handler` will
    be called with that algorithm as argument.
    Results are collected as a sequence of :class:`AccountantRecord`.

    Call :meth:`.Algorithm.register` to register an :class:`Accountant` to
    a :class:`Algorithm`. Call :meth:`report` to retrieve collected records.

    For type checking purposes, the :class:`Accountant` has two
    type parameter ``C`` and ``T``. ``C`` is the type of the observed
    :class:`Algorithm`; ``T`` is the type of `.value` in the reported
    :class:`AccountantRecord`.

    Tutorial: :doc:`../guides/examples/accountant`.
    """
    def __init__(self: Self,
                 events: Container[str],
                 handler: Callable[[C], T],
                 watch_automatic_events: bool = False):
        """
        Args:
            events: Events that trigger the :arg:`handler`.

            handler: Callable that takes the attached algorithm as input.

            watch_automatic_events: If ``True``, also call
                :attr:`handler` on :attr:`Algorithm.automatic_events`.
        """
        #: Records collected by the :class:`Accountant`.
        self._records: list[AccountantRecord[T]] = []

        self.events: Container[str] = events

        self.handler: Callable[[C], T] = handler

        #: The attached :class:`Algorithm`.
        self._subject: Optional[C] = None

        self.watch_automatic_events = watch_automatic_events

    def subscribe(self: Self, subject: C) -> None:
        """Machinery.

        :meta private:

        Subscribe for events in a :class:`.Algorithm`.

        Args:
            subject: the :class:`.Algorithm` whose events are monitored by
                this accountant.
        """
        self._subject = subject

    def update(self: Self, event: str) -> None:
        """Machinery.

        :meta private:

        When the attached :class:`.Algorithm` calls :meth:`.Algorithm.update`,
        the latter calls this method on every accountant registered to the
        algorithm.

        When an event matches a key in :attr:`handlers`, call the corresponding
        value with the attached Algorithm as argument. Store the result in
        :attr:`records`.

        Raise:
            RuntimeError: If no :class:`Algorithm` is attached.
        """
        if self._subject is None:
            raise RuntimeError("Accountant updated without a subject.")
        else:
            if event in self.events\
                    or (self.watch_automatic_events
                        and (event in self._subject.automatic_events)):
                self._records.append(
                    AccountantRecord(event,
                                     self._subject.generation,
                                     self.handler(self._subject)))

    def report(self: Self,
               scope: Optional[str | int] = None) -> list[AccountantRecord[T]]:
        """Report collected records.

        Args:
            scope: Option to filter which records to report:

                * If :arg:`scope` is an :class:`int` : report record
                  only if :python:`record.generation==scope`.

                * If :arg:`scope` is an :class:`str` : report record
                  only if :python:`record.event==scope`.

                * Otherwise, of if (by default) ``scope==None``,
                  report all records.

        Each time an event fires in the attached :class:`.Algorithm`,
        if that event is registered in :attr:`handlers`, supply the
        :class:`.Algorithm` to the handler as argument then collect
        the result in an :class:`.AccountantRecord`. This method
        returns a list of all collected records.
        """
        if not self.is_registered():
            raise ValueError("Accountant is not attached to an algorithm;"
                             " cannot publish.")
        if isinstance(scope, int):
            return [r for r in self._records
                    if r.generation == scope]
        if isinstance(scope, str):
            return [r for r in self._records
                    if r.event == scope]
        else:
            return self._records

    def is_registered(self: Self) -> bool:
        """Return if this accountant is attached to an :class:`.Algorithm`.
        """
        return self._subject is not None

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
                    index: int) -> AccountantRecord[T]:
        pass

    @overload
    def __getitem__(self: Self,
                    index: slice) -> Sequence[AccountantRecord[T]]:
        pass

    @override
    def __getitem__(self: Self,
                    index: int | slice)\
            -> AccountantRecord[T] | Sequence[AccountantRecord[T]]:
        return self._records[index]
