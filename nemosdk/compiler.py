from __future__ import annotations

from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET
import json

from .model import (
    BIUNetworkDefaults,
    Layer,
    materialize_precedence,
)


def _append_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = str(text)
    return el


def compile_to_xml(
    defaults: BIUNetworkDefaults,
    layers: list[Layer],
    include_supervisor: bool = False,
    supervisor_defaults: Optional[BIUNetworkDefaults] = None,
) -> tuple[str, Optional[str]]:
    """Produce XML strings for BIU network and optional supervisor.

    Returns (biu_xml_str, supervisor_xml_str|None)
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
) -> tuple[str, Optional[str]]:
    """Python-first name for the compiler. Returns same outputs as compile_to_xml.

    Provided to keep the public API focused on the SDK semantics rather than XML.
    """
    return compile_to_xml(
        defaults=defaults,
        layers=layers,
        include_supervisor=include_supervisor,
        supervisor_defaults=supervisor_defaults,
    )


def build_run_config(
    *,
    output_directory: Path,
    xml_config_path: Path,
    data_input_file: Path,
    sup_xml_config_path: Optional[Path] = None,
    synapses_energy_table_path: Optional[Path] = None,
    neuron_energy_table_path: Optional[Path] = None,
    relativize_from: Optional[Path] = None,
) -> dict:
    """Construct a NemoSim run config.json dict matching repo examples.

    If relativize_from is provided, all paths are converted to relative paths from that
    directory (matching simulator working directory conventions).
    """
    def to_rel(p: Optional[Path]) -> Optional[str]:
        if p is None:
            return None
        if relativize_from is None:
            return str(p)
        return str(Path(os_path_relativize(p, relativize_from)))

    cfg: dict[str, str] = {
        "output_directory": to_rel(output_directory) or "",
        "xml_config_path": to_rel(xml_config_path) or "",
        "data_input_file": to_rel(data_input_file) or "",
    }
    if sup_xml_config_path is not None:
        cfg["sup_xml_config_path"] = to_rel(sup_xml_config_path) or ""
    if synapses_energy_table_path is not None:
        cfg["synapses_energy_table_path"] = to_rel(synapses_energy_table_path) or ""
    if neuron_energy_table_path is not None:
        cfg["neuron_energy_table_path"] = to_rel(neuron_energy_table_path) or ""
    return cfg


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def os_path_relativize(p: Path, base: Path) -> Path:
    # Produce a relative path from base to p, even if it requires ".." segments
    p_abs = p if p.is_absolute() else (base / p).resolve()
    try:
        return Path(str(p_abs.resolve())).relative_to(base.resolve())
    except Exception:
        # Fallback to relpath semantics
        import os as _os
        return Path(_os.path.relpath(str(p_abs), str(base.resolve())))


