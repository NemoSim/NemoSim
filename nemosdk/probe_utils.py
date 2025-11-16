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
    wait_for_file: bool = False,
    wait_timeout: Optional[float] = None,
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
        wait_for_file: When True, keep polling for the signal file until it appears.
        wait_timeout: Optional timeout (seconds) when waiting for the file. Ignored if ``wait_for_file`` is False.

    Yields:
        Numeric samples parsed from the underlying output files.

    Raises:
        FileNotFoundError: If the requested signal file does not exist and waiting is disabled.
        TimeoutError: If waiting for the file exceeds ``wait_timeout``.
        ValueError: If an unsupported signal is requested.
    """

    path: Path = probe._signal_path(signal, neuron_idx)  # type: ignore[attr-defined]
    if signal not in probe.available_signals():
        raise ValueError(f"Unsupported signal '{signal}'. Valid options: {probe.available_signals()}")

    if not path.exists():
        if not wait_for_file:
            raise FileNotFoundError(f"{signal} file not found: {path}")
        deadline: Optional[float] = None
        if wait_timeout is not None:
            deadline = time.monotonic() + wait_timeout
        while not path.exists():
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for {signal} file: {path}"
                )
            time.sleep(poll_interval)

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
