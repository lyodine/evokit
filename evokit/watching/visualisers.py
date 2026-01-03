from .watcher import WatcherRecord
from typing import Sequence
# Hello Any my old friend.
# Pyright made me talk with you again.
# Pyright in "strict" mode requires all type parameters
#   to be explicitly given. Any is the safest choice.
from typing import Any
import matplotlib.pyplot as plt

from .._utils.addons import ensure_installed

ensure_installed("numpy")


def plot(records: Sequence[WatcherRecord[tuple[float, ...]]],
         track_generation: bool = False,
         use_line: bool = False,
         *args: Any,
         **kwargs: Any):
    """Plot a sequence of :class:`WatcherRecord`s. Plot
    :attr:`WatcherRecord.value` against :attr:`WatcherRecord.time`.
    Also set the X axis label.

    Args:
        records: Sequence of records. Each
            :attr:`WatcherRecord.value` must only hold either
            :class:`float` or a 1-tuple of type `tuple[float]`.

        track_generation: If ``True``, then also plot values collected
            at ``"STEP_BEGIN"`` and ``"STEP_END"`` as bigger (``s=50``),
            special (``marker="*"``) markers. Otherwise,
            plot them as any other values.

        use_line: If ``True``, then plot a line plot. Otherwise,
            plot a scatter graph.

        args: Passed to :meth:`matplotlib.plot`.

        kwargs: Passed to :meth:`matplotlib.plot`.

    .. note::
        The parameter :arg:`use_line` is provided for convenience.
        Since some values might be ``nan``, plotting and connecting
        only available data points could produce misleading plots.
    """

    records = sorted(records, key=lambda x: x.time)
    start_time: float = records[0].time

    valid_records = [r for r in records
                     if (not any(x != x for x in r.value))]

    valid_times = tuple(r.time - start_time for r in valid_records)
    valid_values = tuple(r.value[0] for r in valid_records)

    if use_line:
        plt.plot(  # type: ignore[reportUnknownMemberType]
            valid_times, valid_values, *args, **kwargs)
    else:
        plt.scatter(  # type: ignore[reportUnknownMemberType]
            valid_times, valid_values, *args, **kwargs)

    if track_generation:
        gen_records = [r for r in valid_records
                       if r.event == "STEP_BEGIN" or r.event == "STEP_END"]
        gen_times = tuple(r.time - start_time for r in gen_records)
        print(min(valid_values))
        print(max(valid_values))
        plt.vlines(gen_times,
                   ymin=min(valid_values),
                   ymax=max(valid_values),
                   colors="#696969",  # type: ignore[reportArgumentType]
                   linestyles="dashed",
                   linewidth=0.5)

        plt.scatter([], [], s=80,
                    color="#696969",
                    marker="|",  # type: ignore[reportArgumentType]
                    label="Generation Barrier")

    plt.legend()
    plt.xlabel("Time (sec)")  # type: ignore[reportUnknownMemberType]
