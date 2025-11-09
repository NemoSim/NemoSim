from __future__ import annotations

"""Utility helpers for working with probe data in real time."""

from pathlib import Path
from typing import Iterator, Optional
import time

from .compiler import LayerProbe


def watch_probe(
    probe: LayerProbe,
    signal: str,
    neuron_idx: int,
    *,
    follow: bool = False,
    poll_interval: float = 0.5,
    max_events: Optional[int] = None,
) -> Iterator[int | float]:
    """Yield values from a probe's signal file, optionally following new data.

    Args:
        probe: The `LayerProbe` to read from.
        signal: One of ``"spikes"``, ``"vin"``, or ``"vns"``.
        neuron_idx: Neuron index within the probed layer (0-based).
        follow: When True, keep tailing the file for new samples (like ``tail -f``).
        poll_interval: Sleep duration between EOF checks when ``follow`` is True.
        max_events: Optional maximum number of samples to yield. When provided,
            iteration stops after this many samples even if ``follow`` is True.

    Yields:
        Numeric samples parsed from the underlying output files.

    Raises:
        FileNotFoundError: If the requested signal file does not exist yet.
        ValueError: If an unsupported signal is requested.
    """

    path: Path = probe._signal_path(signal, neuron_idx)  # type: ignore[attr-defined]
    if not path.exists():
        raise FileNotFoundError(f"{signal} file not found: {path}")

    if signal not in probe.available_signals():
        raise ValueError(f"Unsupported signal '{signal}'. Valid options: {probe.available_signals()}")

    caster = probe._SIGNAL_CASTERS[signal]  # type: ignore[attr-defined]
    yielded = 0

    with path.open() as fh:
        while True:
            line = fh.readline()
            if line:
                value_str = line.strip()
                if not value_str:
                    continue
                value = caster(value_str)
                yield value
                yielded += 1
                if max_events is not None and yielded >= max_events:
                    break
            else:
                if not follow:
                    break
                if max_events is not None and yielded >= max_events:
                    break
                time.sleep(poll_interval)
