from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Dict
import xml.etree.ElementTree as ET
import json

from .model import (
    BIUNetworkDefaults,
    Layer,
    materialize_precedence,
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
    supervisor_defaults: Optional[BIUNetworkDefaults] = None,
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
    supervisor_defaults
        Optional defaults used when emitting the supervisor XML.

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
        sdef = supervisor_defaults or BIUNetworkDefaults()
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


def compile(
    defaults: BIUNetworkDefaults,
    layers: list[Layer],
    include_supervisor: bool = False,
    supervisor_defaults: Optional[BIUNetworkDefaults] = None,
    *,
    # Optional artifact writing in one step for a 2-line compile→run flow
    out_dir: Optional[Path] = None,
    data_input_file: Optional[Path] = None,
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
    # Validate probe uniqueness
    probe_to_layer: Dict[str, int] = {}
    for layer_idx, layer in enumerate(layers):
        if layer.probe is not None:
            if layer.probe in probe_to_layer:
                raise ValueError(
                    f"Duplicate probe name '{layer.probe}': "
                    f"used by layer {probe_to_layer[layer.probe]} and layer {layer_idx}"
                )
            probe_to_layer[layer.probe] = layer_idx

    biu_xml, sup_xml = compile_to_xml(
        defaults=defaults,
        layers=layers,
        include_supervisor=include_supervisor,
        supervisor_defaults=supervisor_defaults,
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

    if data_input_file is None:
        raise ValueError("data_input_file must be provided when out_dir is specified")
    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=biu_xml_path,
        data_input_file=data_input_file,
        sup_xml_config_path=sup_xml_path,
        synapses_energy_table_path=synapses_energy_table_path,
        neuron_energy_table_path=neuron_energy_table_path,
    )
    cfg_path = out_dir / "config.json"
    write_json(cfg_path, cfg)
    return CompiledModel(config_path=cfg_path, probe_to_layer=probe_to_layer)


class LayerProbe:
    """Provides easy access to layer output data by probe name.
    
    After a simulation run, use this to access spikes, vin, and vns data
    for a specific layer without manually opening files.
    """
    
    def __init__(self, layer_idx: int, output_dir: Path):
        """Initialize a layer probe.
        
        Args:
            layer_idx: The layer index (0-based)
            output_dir: Path to the simulation output directory
        """
        self.layer_idx = layer_idx
        self.output_dir = output_dir
    
    def get_spikes(self, neuron_idx: int) -> list[int]:
        """Get spike data for a specific neuron in this layer.
        
        Args:
            neuron_idx: Neuron index within the layer (0-based)
            
        Returns:
            List of spike values (0 or 1) for each time step
        """
        spike_file = self.output_dir / f"spikes_{self.layer_idx}_{neuron_idx}.txt"
        if not spike_file.exists():
            raise FileNotFoundError(f"Spike file not found: {spike_file}")
        with spike_file.open() as f:
            return [int(line.strip()) for line in f if line.strip()]
    
    def get_vin(self, neuron_idx: int) -> list[float]:
        """Get synapse input voltage data for a specific neuron.
        
        Args:
            neuron_idx: Neuron index within the layer (0-based)
            
        Returns:
            List of input voltage values for each time step
        """
        vin_file = self.output_dir / f"vin_{self.layer_idx}_{neuron_idx}.txt"
        if not vin_file.exists():
            raise FileNotFoundError(f"Vin file not found: {vin_file}")
        with vin_file.open() as f:
            return [float(line.strip()) for line in f if line.strip()]
    
    def get_vns(self, neuron_idx: int) -> list[float]:
        """Get neural state potential data for a specific neuron.
        
        Args:
            neuron_idx: Neuron index within the layer (0-based)
            
        Returns:
            List of neural state potential values for each time step
        """
        vns_file = self.output_dir / f"vns_{self.layer_idx}_{neuron_idx}.txt"
        if not vns_file.exists():
            raise FileNotFoundError(f"Vns file not found: {vns_file}")
        with vns_file.open() as f:
            return [float(line.strip()) for line in f if line.strip()]
    
    def get_all_spikes(self) -> Dict[int, list[int]]:
        """Get spike data for all neurons in this layer.
        
        Returns:
            Dictionary mapping neuron index to list of spike values
        """
        result: Dict[int, list[int]] = {}
        spike_files = sorted(self.output_dir.glob(f"spikes_{self.layer_idx}_*.txt"))
        for spike_file in spike_files:
            # Extract neuron index from filename: spikes_<layer>_<neuron>.txt
            parts = spike_file.stem.split("_")
            if len(parts) == 3:
                neuron_idx = int(parts[2])
                result[neuron_idx] = self.get_spikes(neuron_idx)
        return result
    
    def get_all_vin(self) -> Dict[int, list[float]]:
        """Get input voltage data for all neurons in this layer.
        
        Returns:
            Dictionary mapping neuron index to list of input voltage values
        """
        result: Dict[int, list[float]] = {}
        vin_files = sorted(self.output_dir.glob(f"vin_{self.layer_idx}_*.txt"))
        for vin_file in vin_files:
            # Extract neuron index from filename: vin_<layer>_<neuron>.txt
            parts = vin_file.stem.split("_")
            if len(parts) == 3:
                neuron_idx = int(parts[2])
                result[neuron_idx] = self.get_vin(neuron_idx)
        return result
    
    def get_all_vns(self) -> Dict[int, list[float]]:
        """Get neural state potential data for all neurons in this layer.
        
        Returns:
            Dictionary mapping neuron index to list of neural state potential values
        """
        result: Dict[int, list[float]] = {}
        vns_files = sorted(self.output_dir.glob(f"vns_{self.layer_idx}_*.txt"))
        for vns_file in vns_files:
            # Extract neuron index from filename: vns_<layer>_<neuron>.txt
            parts = vns_file.stem.split("_")
            if len(parts) == 3:
                neuron_idx = int(parts[2])
                result[neuron_idx] = self.get_vns(neuron_idx)
        return result


class CompiledModel:
    """A compiled, runnable model artifact exposing a config path and probe access.

    This wrapper keeps the runner interface stable without exposing raw paths,
    and provides easy access to layer data via probe names.
    """

    def __init__(self, config_path: Path, probe_to_layer: Optional[Dict[str, int]] = None):
        """Initialize a compiled model.
        
        Args:
            config_path: Path to the config.json file
            probe_to_layer: Optional mapping from probe names to layer indices
        """
        self.config_path = config_path
        self.probe_to_layer: Dict[str, int] = probe_to_layer or {}

    def get_config_path(self) -> Path:
        """Get the path to the config.json file."""
        return self.config_path
    
    def get_probe(self, probe_name: str) -> LayerProbe:
        """Get a LayerProbe for accessing data by probe name.
        
        Args:
            probe_name: The probe name assigned to a layer
            
        Returns:
            LayerProbe instance for accessing the layer's output data
            
        Raises:
            KeyError: If the probe name is not found
            FileNotFoundError: If the output directory doesn't exist
        """
        if probe_name not in self.probe_to_layer:
            raise KeyError(
                f"Probe '{probe_name}' not found. Available probes: {list(self.probe_to_layer.keys())}"
            )
        
        # Read config.json to get output directory
        with self.config_path.open() as f:
            config = json.load(f)
        
        output_dir = Path(config.get("output_directory", ""))
        if not output_dir.exists():
            raise FileNotFoundError(
                f"Output directory not found: {output_dir}. "
                "Simulation may not have been run yet."
            )
        
        layer_idx = self.probe_to_layer[probe_name]
        return LayerProbe(layer_idx=layer_idx, output_dir=output_dir)
    
    def list_probes(self) -> list[str]:
        """List all available probe names.
        
        Returns:
            List of probe names that can be used with get_probe()
        """
        return list(self.probe_to_layer.keys())


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
    data_input_file: Path,
    include_supervisor: bool = False,
    supervisor_defaults: Optional[BIUNetworkDefaults] = None,
    synapses_energy_table_path: Optional[Path] = None,
    neuron_energy_table_path: Optional[Path] = None,
) -> dict:
    """Convenience helper to compile and write artifacts in one step.

    Writes `biu.xml`, optional `supervisor.xml`, and `config.json` into `out_dir`.
    Returns the in‑memory config dict used for `config.json`.
    """
    biu_xml, sup_xml = compile(
        defaults=defaults,
        layers=layers,
        include_supervisor=include_supervisor,
        supervisor_defaults=supervisor_defaults,
    )
    biu_xml_path = out_dir / "biu.xml"
    write_text(biu_xml_path, biu_xml)
    sup_xml_path = None
    if sup_xml is not None:
        sup_xml_path = out_dir / "supervisor.xml"
        write_text(sup_xml_path, sup_xml)

    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=biu_xml_path,
        data_input_file=data_input_file,
        sup_xml_config_path=sup_xml_path,
        synapses_energy_table_path=synapses_energy_table_path,
        neuron_energy_table_path=neuron_energy_table_path,
    )
    write_json(out_dir / "config.json", cfg)
    return cfg


