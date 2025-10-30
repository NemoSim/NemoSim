from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence


@dataclass(slots=True)
class BIUNetworkDefaults:
    """Global BIU defaults under <BIUNetwork>.

    Only the parameters exercised by examples/release notes are modeled here.
    """

    VTh: Optional[float] = None
    RLeak: Optional[float] = None
    refractory: Optional[int] = None
    VDD: Optional[float] = None
    Cn: Optional[float] = None
    Cu: Optional[float] = None
    fclk: Optional[float] = None
    DSBitWidth: Optional[int] = None  # {4, 8}
    DSClockMHz: Optional[float] = None  # > 0
    DSMode: Optional[str] = None  # ThresholdMode | FrequencyMode

    def validate(self) -> None:
        if self.DSBitWidth is not None and self.DSBitWidth not in {4, 8}:
            raise ValueError("DSBitWidth must be 4 or 8")
        if self.DSClockMHz is not None and self.DSClockMHz <= 0:
            raise ValueError("DSClockMHz must be positive")
        if self.DSMode is not None and self.DSMode not in {"ThresholdMode", "FrequencyMode", ""}:
            raise ValueError("DSMode must be 'ThresholdMode' or 'FrequencyMode'")


@dataclass(slots=True)
class Synapses:
    rows: int
    cols: int
    weights: List[List[float]]

    def validate(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("synapses rows and cols must be positive")
        if len(self.weights) != self.rows:
            raise ValueError("weights must contain exactly 'rows' rows")
        for i, row in enumerate(self.weights):
            if len(row) != self.cols:
                raise ValueError(f"weights row {i} must have exactly 'cols' entries")


@dataclass(slots=True)
class NeuronOverrideRange:
    start: int
    end: int  # inclusive
    VTh: Optional[float] = None
    RLeak: Optional[float] = None
    refractory: Optional[int] = None

    def validate(self, layer_size: int) -> None:
        if self.start < 0 or self.end < 0 or self.start > self.end:
            raise ValueError("NeuronRange indices must be valid and start <= end")
        if self.end >= layer_size:
            raise ValueError("NeuronRange end out of bounds for layer size")


@dataclass(slots=True)
class NeuronOverride:
    index: int
    VTh: Optional[float] = None
    RLeak: Optional[float] = None
    refractory: Optional[int] = None

    def validate(self, layer_size: int) -> None:
        if self.index < 0 or self.index >= layer_size:
            raise ValueError("Neuron index out of bounds for layer size")


@dataclass(slots=True)
class Layer:
    size: int
    synapses: Synapses
    ranges: List[NeuronOverrideRange] = field(default_factory=list)
    neurons: List[NeuronOverride] = field(default_factory=list)

    def validate(self) -> None:
        if self.size <= 0:
            raise ValueError("Layer size must be positive")
        self.synapses.validate()
        if self.synapses.rows != self.size:
            raise ValueError("synapses.rows must equal Layer size")
        for r in self.ranges:
            r.validate(self.size)
        for n in self.neurons:
            n.validate(self.size)


def _iter_optional(tag: str, value: Optional[float | int | str]) -> Iterable[tuple[str, str]]:
    if value is None:
        return []
    return [(tag, str(value))]


def materialize_precedence(
    size: int,
    defaults: BIUNetworkDefaults,
    ranges: Sequence[NeuronOverrideRange],
    neurons: Sequence[NeuronOverride],
) -> dict[str, List[Optional[float | int]]]:
    """Compute final per-neuron vectors with precedence: neuron > range > global.

    Returns a dict with keys: VTh, RLeak, refractory each mapping to a list of size 'size'
    with possibly None values where not explicitly set (to be omitted from XML).
    """
    vth: List[Optional[float]] = [defaults.VTh] * size
    rleak: List[Optional[float]] = [defaults.RLeak] * size
    ref: List[Optional[int]] = [defaults.refractory] * size

    for r in ranges:
        if r.VTh is not None:
            for i in range(r.start, r.end + 1):
                vth[i] = r.VTh
        if r.RLeak is not None:
            for i in range(r.start, r.end + 1):
                rleak[i] = r.RLeak
        if r.refractory is not None:
            for i in range(r.start, r.end + 1):
                ref[i] = r.refractory

    for n in neurons:
        if n.VTh is not None:
            vth[n.index] = n.VTh
        if n.RLeak is not None:
            rleak[n.index] = n.RLeak
        if n.refractory is not None:
            ref[n.index] = n.refractory

    return {"VTh": vth, "RLeak": rleak, "refractory": ref}


