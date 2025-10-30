# lif_builder.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Dict, Union
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

Number = Union[float, int]

# ---------------------- Data models ----------------------

@dataclass
class LayerSpec:
    size: int

    def validate(self) -> None:
        if self.size <= 0:
            raise ValueError("Layer size must be > 0")

@dataclass
class YFlashSpec:
    """Weights between layer (k-1) -> layer k.
    Shape: rows = prev layer size, cols = current layer size."""
    to_layer_index: int  # index of destination layer (>=1)
    weights: List[List[Number]]

    def validate(self, prev_size: int, curr_size: int) -> None:
        if self.to_layer_index < 1:
            raise ValueError("YFlash 'to_layer_index' must be >= 1 (first link is into layer 1)")
        if not self.weights or not self.weights[0]:
            raise ValueError("YFlash weights must be a non-empty matrix")
        rows = len(self.weights)
        cols = len(self.weights[0])
        if rows != prev_size:
            raise ValueError(f"YFlash rows ({rows}) must equal previous layer size ({prev_size})")
        for r in self.weights:
            if len(r) != cols:
                raise ValueError("YFlash weights must be a proper rectangular matrix")
        if cols != curr_size:
            raise ValueError(f"YFlash cols ({cols}) must equal destination layer size ({curr_size})")

@dataclass
class LIFNetwork:
    """Builds a LIF XML with optional YFlash matrices between layers."""
    layers: List[LayerSpec] = field(default_factory=list)
    # Parameters per Table (e.g., Cm, Cf, VDD, VTh, K, Rmin, Rmax, gm, dt, IR, ...)
    # Keys become tags under <LIFNetwork>. Values are written as text.
    params: Dict[str, Number] = field(default_factory=dict)
    _yflashes: Dict[int, YFlashSpec] = field(default_factory=dict)  # key = to_layer_index

    # -------- API --------
    def add_layer(self, size: int) -> "LIFNetwork":
        self.layers.append(LayerSpec(size=size))
        return self

    def set_yflash(self, to_layer_index: int, weights: List[List[Number]]) -> "LIFNetwork":
        """Attach a YFlash between layer (to_layer_index-1) and to_layer_index."""
        self._yflashes[to_layer_index] = YFlashSpec(to_layer_index=to_layer_index, weights=weights)
        return self

    # -------- Validation --------
    def validate(self) -> None:
        if not self.layers:
            raise ValueError("Network must contain at least one layer")
        for i, layer in enumerate(self.layers):
            layer.validate()
            # Validate YFlash for links that have one
            if i >= 1 and i in self._yflashes:
                self._yflashes[i].validate(self.layers[i-1].size, self.layers[i].size)

    # -------- XML serialization --------
    def to_xml(self) -> ET.ElementTree:
        """
        <NetworkConfig type="LIF">
          <LIFNetwork> ...params... </LIFNetwork>
          <Architecture>
            <Layer size="N0"/>
            <YFlash rows="N0" cols="N1"><weights><row>...</row>...</weights></YFlash>
            <Layer size="N1"/>
            ...
          </Architecture>
        </NetworkConfig>
        """
        self.validate()

        root = ET.Element("NetworkConfig", {"type": "LIFNetwork"})  # per guide:contentReference[oaicite:1]{index=1}
        lif_node = ET.SubElement(root, "LIFNetwork")
        for k, v in self.params.items():
            tag = k[0].upper() + k[1:]  # Camelize first char for readability
            ET.SubElement(lif_node, tag).text = str(v)

        arch = ET.SubElement(root, "Architecture")

        # Emit: Layer0, (YFlash01), Layer1, (YFlash12), Layer2, ...
        for i, layer in enumerate(self.layers):
            ET.SubElement(arch, "Layer", {"size": str(layer.size)})
            if i >= 1 and i in self._yflashes:
                y = self._yflashes[i]
                rows = len(y.weights)
                cols = len(y.weights[0])
                ynode = ET.SubElement(arch, "YFlash", {"rows": str(rows), "cols": str(cols)})
                wnode = ET.SubElement(ynode, "weights")
                for row in y.weights:
                    ET.SubElement(wnode, "row").text = " ".join(str(x) for x in row)

        return ET.ElementTree(root)

    def save_xml(self, path: Path) -> Path:
        tree = self.to_xml()
        path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

# ---------------------- I/O helpers ----------------------

def write_txt_input(path: Path, series: Sequence[Sequence[Number]]) -> Path:
    """
    LIF TXT input: one line per time step, values for FIRST layer neurons (space-separated).
    Matches the guide's 'TXT file defines neuron values per time step for the first layer'.:contentReference[oaicite:2]{index=2}
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for t in series:
            f.write(" ".join(str(v) for v in t) + "\n")
    return path

def write_run_config(
    path: Path,
    output_directory: Path,
    xml_config_path: Path,
    data_input_file: Path,
    progress_interval_seconds: int = 2,
) -> Path:
    """
    JSON config fields per guide (sup_xml_config_path is BIU-only).:contentReference[oaicite:3]{index=3}
    All paths are made absolute.
    """
    cfg = {
        "output_directory": str(output_directory.resolve()),
        "xml_config_path": str(xml_config_path.resolve()),
        "data_input_file": str(data_input_file.resolve()),
        "progress_interval_seconds": int(progress_interval_seconds),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=4))
    return path

# ---------------------- Runner ----------------------

DEFAULT_SIM_PATH = "/home/avi/projects/NemoSim/bin/Linux/NEMOSIM"

def find_nemosim() -> str:
    """
    Resolution order: env NEMOSIM / NEMOSIM_PATH, default path, PATH.
    """
    candidates = [
        os.environ.get("NEMOSIM"),
        os.environ.get("NEMOSIM_PATH"),
        DEFAULT_SIM_PATH,
        shutil.which("NEMOSIM"),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError(
        "NEMOSIM not found. Set NEMOSIM/NEMOSIM_PATH, or place it at "
        f"{DEFAULT_SIM_PATH}, or add 'NEMOSIM' to PATH."
    )

def run_nemosim(config_path: Path, sim_path: Optional[str] = None, timeout: Optional[int] = None) -> int:
    """
    Run simulator with given JSON config, printing the command and streaming output.
    """
    cfg = str(config_path.resolve())
    if not os.path.isfile(cfg):
        raise FileNotFoundError(f"Config file not found: {cfg}")

    sim = sim_path or find_nemosim()
    cmd = [sim, cfg]
    print("Running:", " ".join(cmd))  # echo the exact command

    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True
    ) as proc:
        try:
            for line in proc.stdout:  # type: ignore[arg-type]
                print(line, end="")
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError(f"NEMOSIM timed out after {timeout} seconds")
    return rc

# ---------------------- Example (optional) ----------------------

if __name__ == "__main__":
    # Example: 3-layer LIF with YFlash links (4 -> 3 -> 2)
    import math

    lif = (
        LIFNetwork(
            params={
                # Common LIF params; adapt to your circuit/model as needed:contentReference[oaicite:4]{index=4}
                "Cm": 1e-6,
                "Cf": 1e-9,
                "VDD": 5.0,
                "VTh": 1.0,
                "dt": 0.001,
                "IR": 1e-10,
            }
        )
        .add_layer(4)  # input layer N0
        .add_layer(3)  # hidden N1
        .add_layer(2)  # output N2
    )

    # YFlash between Layer0->Layer1: shape rows=N0, cols=N1
    y01 = [
        [0.5, -0.1, 0.2],
        [0.0,  0.3, 0.7],
        [-0.2, 0.9, 0.0],
        [0.1, -0.4, 0.8],
    ]
    # YFlash between Layer1->Layer2: rows=N1, cols=N2
    y12 = [
        [ 0.6, -0.3],
        [-0.5,  0.2],
        [ 0.9,  0.1],
    ]
    lif.set_yflash(1, y01).set_yflash(2, y12)

    out_dir = Path("/home/avi/projects/NemoSim/tests/SNN/LIF/example_run").resolve()
    xml_path = out_dir / "net.xml"
    txt_path = out_dir / "input.txt"
    cfg_path = out_dir / "config.json"

    lif.save_xml(xml_path)

    # Build T×N0 input series for first layer
    T, N0 = 100, lif.layers[0].size
    def sig(t, n):
        return 1e-10 * math.sin(2 * math.pi * (0.05 + 0.01*n) * t) + (1e-11 * n)
    series = [[sig(t, n) for n in range(N0)] for t in range(T)]

    write_txt_input(txt_path, series)

    write_run_config(cfg_path, out_dir, xml_path, txt_path, progress_interval_seconds=2)

    # Run
    rc = run_nemosim(cfg_path)
    print("Exit code:", rc)
