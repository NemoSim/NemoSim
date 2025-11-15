from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable as IterableABC
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, Sequence, Union, cast
import xml.etree.ElementTree as ET
import json

from .model import (
    BIUNetworkDefaults,
    Layer,
    materialize_precedence,
)

# Hard-coded supervisor defaults - no longer user-configurable
_DEFAULT_SUPERVISOR_DEFAULTS = BIUNetworkDefaults(
    fclk=1e7,
    RLeak=1e6,
    VDD=1.2,
    Cn=1e-12,
    Cu=4e-15,
)


def _append_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Create a child element under `parent` with stringified text content."""
    el = ET.SubElement(parent, tag)
    el.text = str(text)
    return el


def compile_to_xml(
    defaults: BIUNetworkDefaults,
    layers: list[Layer],
    include_supervisor: bool = False,
) -> tuple[str, Optional[str]]:
    """Produce XML strings for a BIU network and an optional supervisor file.

    Parameters
    ----------
    defaults
        Global network defaults to emit under `<BIUNetwork>`.
    layers
        Ordered list of layers to emit under `<Architecture>`.
    include_supervisor
        Whether to also emit a separate supervisor XML string.

    Returns
    -------
    tuple[str, Optional[str]]
        `(biu_xml, supervisor_xml)` where `supervisor_xml` is None when not requested.
    """
    # Validate inputs early
    defaults.validate()
    for lyr in layers:
        lyr.validate()

    # Root NetworkConfig for BIU
    root = ET.Element("NetworkConfig", {"type": "BIUNetwork"})
    biu = ET.SubElement(root, "BIUNetwork")

    # Global defaults under <BIUNetwork>
    if defaults.VTh is not None:
        _append_text(biu, "VTh", defaults.VTh)
    if defaults.RLeak is not None:
        _append_text(biu, "RLeak", defaults.RLeak)
    if defaults.refractory is not None:
        _append_text(biu, "refractory", defaults.refractory)
    if defaults.VDD is not None:
        _append_text(biu, "VDD", defaults.VDD)
    if defaults.Cn is not None:
        _append_text(biu, "Cn", defaults.Cn)
    if defaults.Cu is not None:
        _append_text(biu, "Cu", defaults.Cu)
    if defaults.fclk is not None:
        _append_text(biu, "fclk", defaults.fclk)
    if defaults.DSClockMHz is not None:
        if defaults.DSClockMHz <= 0:
            raise ValueError("DSClockMHz must be positive")
        _append_text(biu, "DSClockMHz", defaults.DSClockMHz)
    if defaults.DSBitWidth is not None:
        if defaults.DSBitWidth not in {4, 8}:
            raise ValueError("DSBitWidth must be 4 or 8")
        _append_text(biu, "DSBitWidth", defaults.DSBitWidth)
    # DSMode defaulting: missing or empty -> ThresholdMode (informational)
    if defaults.DSMode is None or defaults.DSMode == "":
        _append_text(biu, "DSMode", "ThresholdMode")
    else:
        if defaults.DSMode not in {"ThresholdMode", "FrequencyMode"}:
            raise ValueError("DSMode must be 'ThresholdMode' or 'FrequencyMode'")
        _append_text(biu, "DSMode", defaults.DSMode)

    arch = ET.SubElement(root, "Architecture")

    for lyr in layers:
        l_el = ET.SubElement(arch, "Layer", {"size": str(lyr.size)})
        # Synapses
        syn = ET.SubElement(l_el, "synapses", {"rows": str(lyr.synapses.rows), "cols": str(lyr.synapses.cols)})
        w = ET.SubElement(syn, "weights")
        if len(lyr.synapses.weights) == 0:
            raise ValueError("Missing required <weights> rows under <synapses>")
        for row in lyr.synapses.weights:
            row_str = " ".join(str(v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v) for v in row)
            _append_text(w, "row", row_str)

        # Per-neuron overrides using precedence
        vectors = materialize_precedence(lyr.size, defaults, lyr.ranges, lyr.neurons)

        # Emit ranges
        for r in lyr.ranges:
            r_el = ET.SubElement(l_el, "NeuronRange", {"start": str(r.start), "end": str(r.end)})
            if r.VTh is not None:
                _append_text(r_el, "VTh", r.VTh)
            if r.RLeak is not None:
                _append_text(r_el, "RLeak", r.RLeak)
            if r.refractory is not None:
                _append_text(r_el, "refractory", r.refractory)

        # Emit neuron-specific overrides last (most specific)
        for n in lyr.neurons:
            n_el = ET.SubElement(l_el, "Neuron", {"index": str(n.index)})
            if n.VTh is not None:
                _append_text(n_el, "VTh", n.VTh)
            if n.RLeak is not None:
                _append_text(n_el, "RLeak", n.RLeak)
            if n.refractory is not None:
                _append_text(n_el, "refractory", n.refractory)

    # Serialize BIU network XML
    biu_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    sup_xml: Optional[str] = None
    if include_supervisor:
        sup_root = ET.Element("NetworkConfig", {"type": "BIUNetwork"})
        sup_biu = ET.SubElement(sup_root, "BIUNetwork")
        sdef = _DEFAULT_SUPERVISOR_DEFAULTS
        # Only analog-ish defaults are typical in supervisor examples
        if sdef.fclk is not None:
            _append_text(sup_biu, "fclk", sdef.fclk)
        if sdef.RLeak is not None:
            _append_text(sup_biu, "RLeak", sdef.RLeak)
        if sdef.VDD is not None:
            _append_text(sup_biu, "VDD", sdef.VDD)
        if sdef.Cn is not None:
            _append_text(sup_biu, "Cn", sdef.Cn)
        if sdef.Cu is not None:
            _append_text(sup_biu, "Cu", sdef.Cu)
        sup_xml = ET.tostring(sup_root, encoding="utf-8", xml_declaration=True).decode("utf-8")

    return biu_xml, sup_xml


@dataclass(slots=True)
class ProbeMetadata:
    """Metadata describing a probe and its associated layer."""

    name: str
    layer_index: int
    layer_size: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "name": self.name,
            "layer_index": self.layer_index,
            "layer_size": self.layer_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProbeMetadata":
        return cls(
            name=data["name"],
            layer_index=int(data["layer_index"]),
            layer_size=int(data["layer_size"]),
        )


def _safe_min(current: Optional[float], value: float) -> float:
    if current is None:
        return value
    return value if value < current else current


def _safe_max(current: Optional[float], value: float) -> float:
    if current is None:
        return value
    return value if value > current else current


def _collect_probe_metadata(layers: Sequence[Layer]) -> tuple[Dict[str, int], Dict[str, ProbeMetadata]]:
    """Validate probe uniqueness and collect metadata for persistence."""
    probe_to_layer: Dict[str, int] = {}
    probe_metadata: Dict[str, ProbeMetadata] = {}

    for layer_idx, layer in enumerate(layers):
        if layer.probe is None:
            continue
        name = layer.probe.strip()
        if not name:
            raise ValueError(f"Probe name for layer {layer_idx} must be a non-empty string")
        if name in probe_to_layer:
            raise ValueError(
                f"Duplicate probe name '{layer.probe}': "
                f"used by layer {probe_to_layer[layer.probe]} and layer {layer_idx}"
            )
        probe_to_layer[name] = layer_idx
        probe_metadata[name] = ProbeMetadata(
            name=name,
            layer_index=layer_idx,
            layer_size=layer.size,
        )

    return probe_to_layer, probe_metadata


def compile(
    defaults: BIUNetworkDefaults,
    layers: list[Layer],
    include_supervisor: bool = False,
    *,
    # Optional artifact writing in one step for a 2-line compile→run flow
    out_dir: Optional[Path] = None,
    data_input_file: Optional[Path] = None,
    input_data: Optional[Iterable[int | float]] = None,
    synapses_energy_table_path: Optional[Path] = None,
    neuron_energy_table_path: Optional[Path] = None,
) -> Union[tuple[str, Optional[str]], "CompiledModel"]:
    """Compile a BIU model into XML, optionally writing runnable artifacts.

    Behavior
    --------
    - If `out_dir` is None: returns `(biu_xml, supervisor_xml)` strings.
    - If `out_dir` is provided: writes `biu.xml`, optional `supervisor.xml`, and
      `config.json`, then returns a `CompiledModel` with the config path.
    """
    if input_data is not None and out_dir is None:
        raise ValueError("input_data requires out_dir to be provided")
    if input_data is not None and data_input_file is not None:
        raise ValueError("Provide either data_input_file or input_data, not both")

    # Validate probe uniqueness and persist metadata
    probe_to_layer, probe_metadata = _collect_probe_metadata(layers)

    biu_xml, sup_xml = compile_to_xml(
        defaults=defaults,
        layers=layers,
        include_supervisor=include_supervisor,
    )
    if out_dir is None:
        return biu_xml, sup_xml

    # Write artifacts and return config path
    out_dir.mkdir(parents=True, exist_ok=True)
    biu_xml_path = out_dir / "biu.xml"
    write_text(biu_xml_path, biu_xml)
    sup_xml_path = None
    if sup_xml is not None:
        sup_xml_path = out_dir / "supervisor.xml"
        write_text(sup_xml_path, sup_xml)

    input_path: Optional[Path] = None
    if input_data is not None:
        input_path = out_dir / "input.txt"
        write_input_data(input_path, input_data)
    elif data_input_file is not None:
        input_path = Path(data_input_file)
    if input_path is None:
        raise ValueError(
            "data_input_file must be provided when out_dir is specified (or supply input_data)"
        )

    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=biu_xml_path,
        data_input_file=input_path,
        sup_xml_config_path=sup_xml_path,
        synapses_energy_table_path=synapses_energy_table_path,
        neuron_energy_table_path=neuron_energy_table_path,
    )
    cfg_path = out_dir / "config.json"
    write_json(cfg_path, cfg)

    # Persist probe metadata alongside artifacts for later inspection
    if probe_metadata:
        probes_path = out_dir / "probes.json"
        write_json(
            probes_path,
            {
                "probes": [meta.to_dict() for meta in probe_metadata.values()],
            },
        )

    return CompiledModel(
        config_path=cfg_path,
        probe_to_layer=probe_to_layer,
        probe_metadata=probe_metadata,
    )


class LayerProbe:
    """Provides easy access to layer output data by probe name.

    After a simulation run, use this to access spikes, vin, and vns data
    for a specific layer without manually opening files. Additional helpers
    expose chunked iteration, pandas DataFrame conversion, and metadata.
    """

    _SIGNAL_CASTERS: Dict[str, Callable[[str], int | float]] = {
        "spikes": int,
        "vin": float,
        "vns": float,
    }

    def __init__(self, layer_idx: int, output_dir: Path, metadata: Optional[ProbeMetadata] = None):
        """Initialize a layer probe.

        Args:
            layer_idx: The layer index (0-based)
            output_dir: Path to the simulation output directory
            metadata: Optional probe metadata (layer size, etc.)
        """
        self.layer_idx = layer_idx
        self.output_dir = output_dir
        self.metadata = metadata

    # ------------------------------------------------------------------
    # Core accessors
    # ------------------------------------------------------------------
    def get_spikes(self, neuron_idx: int) -> list[int]:
        """Get spike data for a specific neuron in this layer."""
        return cast(list[int], self._read_signal("spikes", neuron_idx))

    def get_vin(self, neuron_idx: int) -> list[float]:
        """Get synapse input voltage data for a specific neuron."""
        return cast(list[float], self._read_signal("vin", neuron_idx))

    def get_vns(self, neuron_idx: int) -> list[float]:
        """Get neural state potential data for a specific neuron."""
        return cast(list[float], self._read_signal("vns", neuron_idx))

    def get_all_spikes(self) -> Dict[int, list[int]]:
        """Get spike data for all neurons in this layer."""
        return cast(Dict[int, list[int]], self._load_all_signal("spikes"))

    def get_all_vin(self) -> Dict[int, list[float]]:
        """Get input voltage data for all neurons in this layer."""
        return cast(Dict[int, list[float]], self._load_all_signal("vin"))

    def get_all_vns(self) -> Dict[int, list[float]]:
        """Get neural state potential data for all neurons in this layer."""
        return cast(Dict[int, list[float]], self._load_all_signal("vns"))

    # ------------------------------------------------------------------
    # Chunked iteration helpers
    # ------------------------------------------------------------------
    def iter_spikes(self, neuron_idx: int, *, chunk_size: int = 1024) -> Iterator[list[int]]:
        """Iterate over spike data in chunks for the specified neuron."""
        for chunk in self._iter_signal("spikes", neuron_idx, chunk_size=chunk_size):
            yield cast(list[int], chunk)

    def iter_vin(self, neuron_idx: int, *, chunk_size: int = 1024) -> Iterator[list[float]]:
        """Iterate over input voltage data in chunks for the specified neuron."""
        for chunk in self._iter_signal("vin", neuron_idx, chunk_size=chunk_size):
            yield cast(list[float], chunk)

    def iter_vns(self, neuron_idx: int, *, chunk_size: int = 1024) -> Iterator[list[float]]:
        """Iterate over neural state data in chunks for the specified neuron."""
        for chunk in self._iter_signal("vns", neuron_idx, chunk_size=chunk_size):
            yield cast(list[float], chunk)

    def iter_all_spikes(self, *, chunk_size: int = 1024) -> Iterator[tuple[int, list[int]]]:
        """Iterate over all spike files, yielding (neuron_idx, chunk)."""
        for neuron_idx in self._list_neuron_indices(signal="spikes"):
            for chunk in self.iter_spikes(neuron_idx, chunk_size=chunk_size):
                yield neuron_idx, chunk

    def stream(
        self,
        signal: str,
        *,
        neurons: Optional[Sequence[int]] = None,
        chunk_size: int = 1024,
    ) -> Iterator[tuple[int, list[int | float]]]:
        """Stream signal data in chunks for the specified neurons.

        Yields tuples of ``(neuron_idx, chunk)``, where ``chunk`` is a list of values.
        """
        neuron_indices = list(neurons) if neurons is not None else self._list_neuron_indices(signal=signal)
        for neuron_idx in neuron_indices:
            for chunk in self._iter_signal(signal, neuron_idx, chunk_size=chunk_size):
                yield neuron_idx, chunk

    def summarize(
        self,
        signal: str,
        *,
        neurons: Optional[Sequence[int]] = None,
        chunk_size: int = 4096,
    ) -> dict[int, dict[str, float | int | None]]:
        """Compute streaming summary statistics for the requested signal.

        Returns a mapping of neuron index to summary statistics. Statistics include:
        ``count``, ``min``, ``max``, ``sum``, ``mean`` and ``spikes`` (the latter only
        for the ``spikes`` signal).
        """
        neuron_indices = list(neurons) if neurons is not None else self._list_neuron_indices(signal=signal)
        results: dict[int, dict[str, float | int | None]] = {}

        for neuron_idx in neuron_indices:
            count = 0
            total = 0.0
            minimum: Optional[float] = None
            maximum: Optional[float] = None
            spike_sum: Optional[int] = 0 if signal == "spikes" else None

            for chunk in self._iter_signal(signal, neuron_idx, chunk_size=chunk_size):
                for value in chunk:
                    as_float = float(value)
                    count += 1
                    total += as_float
                    minimum = _safe_min(minimum, as_float)
                    maximum = _safe_max(maximum, as_float)
                    if spike_sum is not None:
                        spike_sum += int(value)

            mean = total / count if count > 0 else None
            results[neuron_idx] = {
                "count": count,
                "min": minimum,
                "max": maximum,
                "sum": total if count > 0 else 0.0,
                "mean": mean,
            }
            if spike_sum is not None:
                results[neuron_idx]["spikes"] = spike_sum

        return results

    # ------------------------------------------------------------------
    # DataFrame helper
    # ------------------------------------------------------------------
    def to_dataframe(
        self,
        *,
        neurons: Optional[Sequence[int]] = None,
        signals: Sequence[str] = ("spikes", "vin", "vns"),
        sample_every: int = 1,
        max_rows: Optional[int] = None,
    ):
        """Return selected signals as a pandas DataFrame.

        Args:
            neurons: Optional subset of neuron indices to include. Defaults to all.
            signals: Iterable of signal names ("spikes", "vin", "vns").
            sample_every: Down-sample by keeping every N-th sample (>= 1).
            max_rows: Optional maximum number of rows to keep.

        Returns:
            pandas.DataFrame with one column per (signal, neuron) pair.

        Raises:
            RuntimeError: If pandas is not installed.
            ValueError: If sample_every < 1 or signal lengths mismatch.
        """
        if sample_every < 1:
            raise ValueError("sample_every must be >= 1")

        try:
            import pandas as pd  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "pandas is required for LayerProbe.to_dataframe(); "
                "install it via 'pip install pandas'."
            ) from exc

        neuron_indices = list(neurons) if neurons is not None else self._list_neuron_indices()
        if not neuron_indices or not signals:
            return pd.DataFrame()

        data: dict[str, list[int | float]] = {}
        expected_length: Optional[int] = None

        for signal in signals:
            for neuron_idx in neuron_indices:
                series = self._read_signal(signal, neuron_idx)
                if sample_every > 1:
                    series = series[::sample_every]
                if max_rows is not None:
                    series = series[:max_rows]
                key = f"{signal}_n{neuron_idx}"
                data[key] = series
                expected_length = expected_length or len(series)
                if len(series) != expected_length:
                    raise ValueError(
                        f"Signal length mismatch for {key}: expected {expected_length}, got {len(series)}"
                    )

        return pd.DataFrame(data)

    # ------------------------------------------------------------------
    # Metadata & utilities
    # ------------------------------------------------------------------
    def available_signals(self) -> tuple[str, ...]:
        """Tuple of supported signal names."""
        return tuple(self._SIGNAL_CASTERS.keys())

    def layer_size(self) -> Optional[int]:
        """Return expected number of neurons when available."""
        return self.metadata.layer_size if self.metadata else None

    def list_neuron_indices(self) -> list[int]:
        """Return sorted neuron indices detected for this probe."""
        return self._list_neuron_indices()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _signal_path(self, signal: str, neuron_idx: int) -> Path:
        if signal not in self._SIGNAL_CASTERS:
            raise ValueError(f"Unsupported signal '{signal}'. Valid options: {tuple(self._SIGNAL_CASTERS)}")
        return self.output_dir / f"{signal}_{self.layer_idx}_{neuron_idx}.txt"

    def _read_signal(self, signal: str, neuron_idx: int) -> list[int] | list[float]:
        path = self._signal_path(signal, neuron_idx)
        if not path.exists():
            raise FileNotFoundError(f"{signal} file not found: {path}")
        caster = self._SIGNAL_CASTERS[signal]
        with path.open() as fh:
            return [caster(line.strip()) for line in fh if line.strip()]

    def _iter_signal(self, signal: str, neuron_idx: int, *, chunk_size: int) -> Iterator[list[int | float]]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        path = self._signal_path(signal, neuron_idx)
        if not path.exists():
            raise FileNotFoundError(f"{signal} file not found: {path}")
        caster = self._SIGNAL_CASTERS[signal]
        chunk: list[int | float] = []
        with path.open() as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                chunk.append(caster(line))
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
        if chunk:
            yield chunk

    def _load_all_signal(self, signal: str) -> Dict[int, list[int | float]]:
        data: Dict[int, list[int | float]] = {}
        for neuron_idx in self._list_neuron_indices(signal=signal):
            try:
                data[neuron_idx] = self._read_signal(signal, neuron_idx)
            except FileNotFoundError:
                continue
        return data

    def _list_neuron_indices(self, signal: Optional[str] = None) -> list[int]:
        if self.metadata is not None:
            return list(range(self.metadata.layer_size))

        pattern_signal = signal or "spikes"
        pattern = f"{pattern_signal}_{self.layer_idx}_*.txt"
        indices: set[int] = set()
        for path in self.output_dir.glob(pattern):
            parts = path.stem.split("_")
            if len(parts) == 3:
                try:
                    indices.add(int(parts[2]))
                except ValueError:
                    continue
        return sorted(indices)


class CompiledModel:
    """A compiled, runnable model artifact exposing a config path and probe access.

    This wrapper keeps the runner interface stable without exposing raw paths,
    and provides easy access to layer data via probe names.
    """

    def __init__(
        self,
        config_path: Path,
        probe_to_layer: Optional[Dict[str, int]] = None,
        probe_metadata: Optional[Dict[str, ProbeMetadata]] = None,
    ):
        """Initialize a compiled model.

        Args:
            config_path: Path to the config.json file
            probe_to_layer: Optional mapping from probe names to layer indices
            probe_metadata: Optional mapping from probe names to ProbeMetadata
        """
        self.config_path = config_path
        self.probe_to_layer: Dict[str, int] = probe_to_layer or {}
        self.probe_metadata: Dict[str, ProbeMetadata] = probe_metadata or {}
        self._config_cache: Optional[dict[str, Any]] = None

        if not self.probe_to_layer or not self.probe_metadata:
            self._load_probe_metadata_from_disk()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_config_path(self) -> Path:
        """Get the path to the config.json file."""
        return self.config_path

    def get_probe(self, probe_name: str) -> LayerProbe:
        """Get a LayerProbe for accessing data by probe name."""
        if probe_name not in self.probe_to_layer:
            raise KeyError(
                f"Probe '{probe_name}' not found. Available probes: {self.list_probes()}"
            )

        output_dir = self._get_output_directory()

        layer_idx = self.probe_to_layer[probe_name]
        metadata = self.probe_metadata.get(probe_name)
        return LayerProbe(layer_idx=layer_idx, output_dir=output_dir, metadata=metadata)

    def list_probes(self) -> list[str]:
        """List all available probe names sorted alphabetically."""
        return sorted(self.probe_to_layer.keys())

    def get_probe_metadata(self, probe_name: str) -> ProbeMetadata:
        """Return metadata for a specific probe."""
        if probe_name not in self.probe_metadata:
            raise KeyError(
                f"Probe '{probe_name}' metadata not found. Available probes: {self.list_probes()}"
            )
        return self.probe_metadata[probe_name]

    def list_probe_metadata(self) -> list[ProbeMetadata]:
        """Return metadata for all probes."""
        return [self.probe_metadata[name] for name in self.list_probes()]

    def get_probe_layer_index(self, probe_name: str) -> int:
        """Return the layer index associated with a probe."""
        if probe_name not in self.probe_to_layer:
            raise KeyError(
                f"Probe '{probe_name}' not found. Available probes: {self.list_probes()}"
            )
        return self.probe_to_layer[probe_name]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_config(self) -> dict[str, Any]:
        if self._config_cache is None:
            with self.config_path.open() as fh:
                self._config_cache = json.load(fh)
        return self._config_cache

    def _get_output_directory(self) -> Path:
        config = self._load_config()
        output_dir = Path(config.get("output_directory", ""))
        if not output_dir.exists():
            raise FileNotFoundError(
                f"Output directory not found: {output_dir}. "
                "Simulation may not have been run yet."
            )
        return output_dir

    def _load_probe_metadata_from_disk(self) -> None:
        probes_path = self.config_path.parent / "probes.json"
        if not probes_path.exists():
            return

        try:
            with probes_path.open() as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse probe metadata at {probes_path}") from exc

        entries = data.get("probes", [])
        for entry in entries:
            meta = ProbeMetadata.from_dict(entry)
            self.probe_metadata.setdefault(meta.name, meta)
            self.probe_to_layer.setdefault(meta.name, meta.layer_index)


def build_run_config(
    *,
    output_directory: Path,
    xml_config_path: Path,
    data_input_file: Path,
    sup_xml_config_path: Optional[Path] = None,
    synapses_energy_table_path: Optional[Path] = None,
    neuron_energy_table_path: Optional[Path] = None,
) -> dict:
    """Construct a `config.json` dict with absolute paths for NemoSim.

    Parameters are written as absolute paths to avoid working‑directory issues.
    Only provided optional paths are included.
    """
    def to_abs(p: Optional[Path]) -> Optional[str]:
        if p is None:
            return None
        return str(p.resolve())

    cfg: dict[str, str] = {
        "output_directory": to_abs(output_directory) or "",
        "xml_config_path": to_abs(xml_config_path) or "",
        "data_input_file": to_abs(data_input_file) or "",
    }
    if sup_xml_config_path is not None:
        cfg["sup_xml_config_path"] = to_abs(sup_xml_config_path) or ""
    if synapses_energy_table_path is not None:
        cfg["synapses_energy_table_path"] = to_abs(synapses_energy_table_path) or ""
    if neuron_energy_table_path is not None:
        cfg["neuron_energy_table_path"] = to_abs(neuron_energy_table_path) or ""
    return cfg


Number = Union[int, float]


def write_input_data(path: Path, data: Iterable[Union[Number, Iterable[Number]]]) -> None:
    """Write input samples to ``path``.

    Each entry can be:
      - a single numeric value -> written as one value per line.
      - an iterable of numeric values -> written space-separated on a single line.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for value in data:
            if isinstance(value, (str, bytes)):
                fh.write(value.rstrip("\n") + "\n")
            elif isinstance(value, IterableABC) and not isinstance(value, (int, float)):
                line = " ".join(str(v) for v in value)
                fh.write(f"{line}\n")
            else:
                fh.write(f"{value}\n")


def write_text(path: Path, content: str) -> None:
    """Write UTF‑8 text to `path`, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    """Write pretty‑printed JSON to `path` (UTF‑8), ensuring parent dirs exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def os_path_relativize(p: Path, base: Path) -> Path:
    # Deprecated in favor of absolute paths; kept for backward compatibility.
    return p


def compile_and_write(
    *,
    defaults: BIUNetworkDefaults,
    layers: list[Layer],
    out_dir: Path,
    data_input_file: Optional[Path] = None,
    input_data: Optional[Iterable[int | float]] = None,
    include_supervisor: bool = False,
    synapses_energy_table_path: Optional[Path] = None,
    neuron_energy_table_path: Optional[Path] = None,
) -> dict:
    """Convenience helper to compile and write artifacts in one step.

    Writes `biu.xml`, optional `supervisor.xml`, and `config.json` into `out_dir`.
    Returns the in‑memory config dict used for `config.json`.
    """
    if input_data is not None and data_input_file is not None:
        raise ValueError("Provide either data_input_file or input_data, not both")

    probe_to_layer, probe_metadata = _collect_probe_metadata(layers)

    biu_xml, sup_xml = compile(
        defaults=defaults,
        layers=layers,
        include_supervisor=include_supervisor,
    )
    biu_xml_path = out_dir / "biu.xml"
    write_text(biu_xml_path, biu_xml)
    sup_xml_path = None
    if sup_xml is not None:
        sup_xml_path = out_dir / "supervisor.xml"
        write_text(sup_xml_path, sup_xml)

    if input_data is not None:
        input_path = out_dir / "input.txt"
        write_input_data(input_path, input_data)
    elif data_input_file is not None:
        input_path = Path(data_input_file)
    else:
        raise ValueError("data_input_file must be provided (or supply input_data)")

    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=biu_xml_path,
        data_input_file=input_path,
        sup_xml_config_path=sup_xml_path,
        synapses_energy_table_path=synapses_energy_table_path,
        neuron_energy_table_path=neuron_energy_table_path,
    )
    write_json(out_dir / "config.json", cfg)

    if probe_metadata:
        write_json(
            out_dir / "probes.json",
            {
                "probes": [meta.to_dict() for meta in probe_metadata.values()],
            },
        )
    return cfg


