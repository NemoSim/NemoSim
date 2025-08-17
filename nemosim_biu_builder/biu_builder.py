# biu_builder.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence
import json
import math
import xml.etree.ElementTree as ET

Number = float | int

@dataclass
class LayerSpec:
    size: int
    # weights: rows x cols matrix for this layer's synapses
    # Convention: rows == layer.size, cols == previous_layer.size (dense)
    weights: List[List[Number]] = field(default_factory=list)

    def validate(self, prev_size: Optional[int]) -> None:
        if self.size <= 0:
            raise ValueError("Layer size must be > 0")
        if prev_size is None:
            # First layer: no incoming synapses required (can be left empty)
            return
        if not self.weights:
            raise ValueError("Missing weights for non-first layer")
        rows = len(self.weights)
        cols = len(self.weights[0]) if rows else 0
        if rows != self.size:
            raise ValueError(f"Weight rows ({rows}) must equal current layer size ({self.size})")
        if any(len(r) != cols for r in self.weights):
            raise ValueError("Weights must be a proper rectangular matrix")
        if cols != prev_size:
            raise ValueError(f"Weight cols ({cols}) must equal previous layer size ({prev_size})")

@dataclass
class BIUNetwork:
    layers: List[LayerSpec] = field(default_factory=list)
    # Optional BIU parameters; leave empty or add as needed
    params: dict = field(default_factory=dict)

    def add_layer(self, size: int, weights: Optional[List[List[Number]]] = None) -> "BIUNetwork":
        self.layers.append(LayerSpec(size=size, weights=weights or []))
        return self

    def set_weights(self, layer_index: int, weights: List[List[Number]]) -> "BIUNetwork":
        if layer_index <= 0:
            raise ValueError("Only non-first layers take incoming weights (layer_index >= 1)")
        self.layers[layer_index].weights = weights
        return self

    def validate(self) -> None:
        prev = None
        for i, layer in enumerate(self.layers):
            layer.validate(prev)
            prev = layer.size
        if not self.layers:
            raise ValueError("Network must contain at least one layer")

    # ---------- Serialization ----------
    def to_xml(self) -> ET.ElementTree:
        """
        Produces:
        <NetworkConfig type="BIU">
          <BIUNetwork> ...optional params... </BIUNetwork>
          <Architecture>
            <Layer size="...">
              <synapses rows="R" cols="C"><weights>...</weights></synapses>
            </Layer>
            ...
          </Architecture>
        </NetworkConfig>
        """
        self.validate()

        root = ET.Element("NetworkConfig", {"type": "BIU"})
        biu_node = ET.SubElement(root, "BIUNetwork")
        # Write optional/known params (e.g., VDD, VTh, refractory, etc.)
        for k, v in self.params.items():
            # UpperCamelCase tags for readability
            tag = k[0].upper() + k[1:]
            ET.SubElement(biu_node, tag).text = str(v)

        arch = ET.SubElement(root, "Architecture")
        prev_size = None
        for layer in self.layers:
            lnode = ET.SubElement(arch, "Layer", {"size": str(layer.size)})
            if prev_size is not None:
                rows = len(layer.weights)
                cols = len(layer.weights[0]) if rows else 0
                snode = ET.SubElement(lnode, "synapses", {"rows": str(rows), "cols": str(cols)})
                wnode = ET.SubElement(snode, "weights")
                for r in layer.weights:
                    ET.SubElement(wnode, "row").text = " ".join(str(x) for x in r)
            prev_size = layer.size

        return ET.ElementTree(root)

    def save_xml(self, path: Path) -> Path:
        tree = self.to_xml()
        path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

# --------- Input TXT generation ----------
def write_txt_input(path: Path, series: Sequence[Sequence[Number]]) -> Path:
    """
    series: iterable of time steps, each a sequence of values for FIRST layer inputs
            Shape = [T][N0], where N0 = network.layers[0].size
    Format: one line per time step, values space-separated (no delimiters).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for t in series:
            f.write(" ".join(str(v) for v in t) + "\n")
    return path

# --------- JSON run-config generation ----------
def write_run_config(
    path: Path,
    output_directory: Path,
    xml_config_path: Path,
    data_input_file: Path,
    progress_interval_seconds: int = 2,
    sup_xml_config_path: Optional[Path] = None,
) -> Path:
    """
    Write config.json with all absolute paths.
    """
    cfg = {
        "output_directory": str(output_directory.resolve()),
        "xml_config_path": str(xml_config_path.resolve()),
        "data_input_file": str(data_input_file.resolve()),
        "progress_interval_seconds": int(progress_interval_seconds),
    }
    if sup_xml_config_path:
        cfg["sup_xml_config_path"] = str(sup_xml_config_path.resolve())

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=4))
    return path


# add to biu_builder.py
import os
import shutil
import subprocess
from typing import Optional

DEFAULT_SIM_PATH = "/home/avi/projects/NemoSim/bin/Linux/NEMOSIM"

def find_nemosim() -> str:
    """
    Resolution order:
      1) env NEMOSIM or NEMOSIM_PATH
      2) DEFAULT_SIM_PATH
      3) shutil.which('NEMOSIM')
    Raises FileNotFoundError if not found or not executable.
    """
    candidates = [
        os.environ.get("NEMOSIM"),
        os.environ.get("NEMOSIM_PATH"),
        DEFAULT_SIM_PATH,
        shutil.which("NEMOSIM"),
    ]
    for c in candidates:
        if not c:
            continue
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError(
        "NEMOSIM binary not found. Set NEMOSIM/NEMOSIM_PATH, "
        f"or place it at {DEFAULT_SIM_PATH}, or add it to PATH as 'NEMOSIM'."
    )

def run_nemosim(config_path: Path, sim_path: Optional[str] = None, timeout: Optional[int] = None) -> int:
    """
    Run the simulator with the given JSON config.
    Streams stdout/stderr live. Returns the process return code.
    """
    cfg = str(config_path.resolve())
    if not os.path.isfile(cfg):
        raise FileNotFoundError(f"Config file not found: {cfg}")

    sim = sim_path or find_nemosim()
    cmd = [sim, cfg]

    # Print the command that will run
    print("Running:", " ".join(cmd))

    # Launch and stream output
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    ) as proc:
        try:
            for line in proc.stdout:  # type: ignore[arg-type]
                print(line, end="")  # stream progress
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError(f"NEMOSIM timed out after {timeout} seconds")
    return rc



# --------- Example usage (keep as reference) ----------
if __name__ == "__main__":
    # --- define your network as before (same code) ---
    net = (
        BIUNetwork(params={"VDD": 1.2, "VTh": 0.4, "refractory": 2})
        .add_layer(4)
        .add_layer(3)
        .add_layer(2)
    )
    w1 = [
        [0.5, -0.2, 0.1, 0.0],
        [0.7,  0.3, 0.2, -0.1],
        [-0.4, 0.9, 0.0, 0.05],
    ]
    w2 = [
        [1.0, -0.7, 0.25],
        [-0.3, 0.6, 0.8],
    ]
    net.set_weights(1, w1).set_weights(2, w2)

    out_dir = Path("./Tests/SNN/BIU/example_run")
    xml_path = out_dir / "test.xml"
    txt_path = out_dir / "input.txt"
    json_path = out_dir / "config.json"

    net.save_xml(xml_path)

    # Build demo input: T time steps × N0 inputs
    import math
    T, N0 = 100, net.layers[0].size
    def example_signal(t, n):
        return 1e-10 * math.sin(2 * math.pi * (0.05 + 0.01*n) * t) + (1e-11 * n)
    series = [[example_signal(t, n) for n in range(N0)] for t in range(T)]
    write_txt_input(txt_path, series)

    write_run_config(
        json_path,
        output_directory=out_dir,
        xml_config_path=xml_path,
        data_input_file=txt_path,
        progress_interval_seconds=2,
        sup_xml_config_path=None,
    )

    print(f"Wrote:\n  XML : {xml_path}\n  TXT : {txt_path}\n  JSON: {json_path}")

    # --- run the simulator ---
    rc = run_nemosim(json_path)  # or run_nemosim(json_path, sim_path="/custom/path/NEMOSIM")
    print(f"NEMOSIM exited with code {rc}")
