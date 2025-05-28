from concurrent.futures import ProcessPoolExecutor
from typing import TypeVar
from typing import Callable
from typing import Sequence
from typing import Optional
from typing import Iterator

import copy

S = TypeVar("S")
A = TypeVar("A")
B = TypeVar("B")


def parallelise_task[S, A, B](
        fn: Callable[[S, A], B],
        self: S,
        iterable: Sequence[A],
        processes: Optional[int | ProcessPoolExecutor] = None,
        share_self: bool = False) -> Sequence[B]:

    if processes is None:
        return [fn(self, each) for each in iterable]

    executor: ProcessPoolExecutor

    if isinstance(processes, int):
        executor = ProcessPoolExecutor(max_workers=processes)
    else:
        assert isinstance(processes, ProcessPoolExecutor)
        executor = processes

    our_selves: list[S | object] = []

    if share_self:
        our_selves = [copy.deepcopy(self)
                      for _ in range(len(iterable))]
    else:
        our_selves = [None for _ in range(len(iterable))]

    nested_results: Iterator[B] =\
        executor.map(fn,
                     our_selves,
                     iterable,
                     timeout=None,
                     chunksize=1)

    return [*nested_results]
