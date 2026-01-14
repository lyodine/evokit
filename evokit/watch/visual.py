from .watcher import WatcherRecord
from typing import Sequence
# Hello Any my old friend.
# Pyright made me talk with you again.
# Pyright in "strict" mode requires all type parameters
#   to be explicitly given. Any is the safest choice.
from typing import Any, Optional
from collections.abc import Collection
import matplotlib.pyplot as plt
from typing import NamedTuple
from .._utils.dependency import ensure_installed
ensure_installed("matplotlib")


class PrintableRecord(NamedTuple):
    time: float
    event: str
    value: tuple[float, ...]


def _printabify(records: Sequence[WatcherRecord[tuple[float, ...]]]
                | Sequence[WatcherRecord[float]]) ->\
        tuple[PrintableRecord, ...]:

    return tuple(
        PrintableRecord(time=record.time,
                        event=record.event,
                        value=record.value
                        if isinstance(record.value, Sequence)
                        else (record.value,))
        for record in records
    )


def plot(records: Sequence[WatcherRecord[tuple[float, ...]]]
         | Sequence[WatcherRecord[float]],
         track_generation: bool = False,
         use_line: bool = False,
         legend: bool = True,
         axes: Optional[plt.Axes] = None,
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
            at ``"STEP_BEGIN"`` and ``"POST_STEP"`` as bigger (``s=50``),
            special (``marker="*"``) markers. Otherwise,
            plot them as any other values.

        use_line: If ``True``, then plot a line plot. Otherwise,
            plot a scatter graph.

        args: Passed to :meth:`matplotlib.plot`.

        kwargs: Passed to :meth:`matplotlib.plot`.

    Effects:
        Plot to the current Matplotlib :class:`Axes`.

    .. note::
        The parameter :arg:`use_line` is provided for convenience.
        Since some values might be ``nan``, plotting and connecting
        only available data points could produce misleading plots.
    """
    axes = plt.gca() if axes is None else axes

    printable_records = _printabify(records)
    printable_records = sorted(printable_records, key=lambda x: x.time)
    start_time: float = records[0].time

    valid_records = [r for r in printable_records
                     if (not any(x != x for x in r.value))]

    valid_times = tuple(r.time - start_time for r in valid_records)

    all_valid_values_mins: set[float] = set()
    all_valid_values_maxs: set[float] = set()

    for i in range(len(valid_records[0].value)):
        valid_values = tuple(r.value[i] for r in valid_records)
        all_valid_values_mins.add(min(valid_values))
        all_valid_values_maxs.add(max(valid_values))

        if use_line:
            axes.plot(  # type: ignore[reportUnknownMemberType]
                valid_times, valid_values, *args, **kwargs)
        else:
            axes.scatter(  # type: ignore[reportUnknownMemberType]
                valid_times, valid_values, *args, **kwargs)

    if track_generation:
        gen_records = [r for r in valid_records
                       if r.event == "POST_STEP"]
        gen_times = tuple(r.time - start_time for r in gen_records)
        axes.vlines(gen_times,
                    ymin=min(all_valid_values_mins),
                    ymax=max(all_valid_values_maxs),
                    colors="#696969",  # type: ignore[reportArgumentType]
                    linestyles="dashed",
                    linewidth=0.5,
                    zorder=-1)
        _plot_generation_barrier_legend(axes)

    if legend:
        axes.legend()
    axes.set_xlabel("Time (sec)")  # type: ignore[reportUnknownMemberType]


def plot_dict(records: Sequence[WatcherRecord[dict[Any, float]]],
              keys: Optional[Collection[Any]] = None,
              track_generation: bool = False,
              legend: bool = True,
              use_line: bool = False,
              axes: Optional[plt.Axes] = None,
              *args: Any,
              **kwargs: Any):
    axes = plt.gca() if axes is None else axes

    if keys is None:
        keys = records[0].value.keys()
    else:
        for key in keys:
            # Sanity check, Just check the first record.
            assert key in records[0].value.keys()

    records = sorted(records, key=lambda x: x.time)

    start_time: float = records[0].time

    valid_records: tuple[WatcherRecord[dict[Any, float]], ...] =\
        tuple(r for r in records
              if (not any(x != x for x in r.value.values())))

    valid_times: tuple[float, ...] = tuple(r.time - start_time
                                           for r in valid_records)
    valid_values: tuple[dict[Any, float], ...] = tuple(r.value
                                                       for r in valid_records)

    all_y_mins: set[float] = set()
    all_y_maxs: set[float] = set()

    for key in keys:
        data: tuple[float, ...] = tuple(v[key] for v in valid_values)
        all_y_mins.add(min(data))
        all_y_maxs.add(max(data))

        if use_line:
            axes.plot(  # type: ignore[reportUnknownMemberType]
                valid_times, data, *args, **kwargs, label=key)
        else:
            axes.scatter(  # type: ignore[reportUnknownMemberType]
                valid_times, data, *args, **kwargs, label=key)

    if track_generation:
        gen_records = [r for r in valid_records
                       if r.event == "POST_STEP"]
        gen_times = tuple(r.time - start_time for r in gen_records)
        axes.vlines(gen_times,
                    ymin=min(all_y_mins),
                    ymax=max(all_y_maxs),
                    colors="#696969",  # type: ignore[reportArgumentType]
                    linestyles="dashed",
                    linewidth=0.5,
                    zorder=-1)
        _plot_generation_barrier_legend(axes)

    axes.legend()
    axes.set_xlabel("Time (sec)")  # type: ignore[reportUnknownMemberType]


def _plot_generation_barrier_legend(axes: plt.Axes):
    """Generation barriers are vertical lines that mark the
    beginning / end of generations.

    Effects:
        Remove labels from existing generation barriers
        (plotted by previous calls to this method), so
        that only one is plotted.
    """
    BARRIER_TEXT: str = "Generation Barrier"
    for possible_scatter_label in axes.collections:
        if possible_scatter_label.get_label() == BARRIER_TEXT:
            possible_scatter_label.remove()

    axes.scatter([], [], s=80,
                 color="#696969",
                 marker="|",  # type: ignore[reportArgumentType]
                 label=BARRIER_TEXT)
