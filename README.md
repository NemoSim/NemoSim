## 🧠 NemoSDK · Lightweight Front‑End for NemoSim

Describe → Compile → Run BIU spiking networks using a clean Python API. No XML editing required.

[![Python](https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-00B16A.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-000000?logo=linux&logoColor=white)](bin/Linux)
[![Status](https://img.shields.io/badge/Status-Alpha-FF6B6B.svg)](#)

For background on the NEMO consortium and platform objectives, visit the project website: [nemo.org.il](https://nemo.org.il/).

### ✨ What it does
- Define BIU networks layer-by-layer with optional per‑neuron overrides (pure Python).
- Validate layer sizes, weight shapes, DS interface settings, and precedence rules.
- Compile your in‑memory model into runnable artifacts behind the scenes.
- Run the simulator for you and capture logs; you only work with Python objects and paths.

### 📦 Install / Requirements
- Python ≥ 3.10, stdlib only (numpy optional, not required).

### 🧰 Public API (Python‑first)
- Model primitives
  - `BIUNetworkDefaults`: global defaults (threshold, leak, refractory, DS settings, etc.)
  - `Layer(size, synapses, ranges=[], neurons=[])`
  - `Synapses(rows, cols, weights)`
  - `NeuronOverrideRange(start, end, VTh=?, RLeak=?, refractory=?)`
  - `NeuronOverride(index, VTh=?, RLeak=?, refractory=?)`
- Build & run helpers
  - `compile(defaults, layers, include_supervisor=False)` → compile (no XML editing required)
  - `build_run_config(...)` → internal runner config (usually used via examples/CLI)
  - `NemoSimRunner(working_dir).run(config_json_path)` → executes the simulator and captures logs
- CLI (optional): `python -m nemosdk.cli` (`build`, `run`, `diag`)

### 🧩 Concepts (SDK view)
- Global defaults: set once in `BIUNetworkDefaults` (e.g., `VTh`, `RLeak`, `refractory`, DS settings).
- Layers: specify `size` and a `Synapses(rows, cols, weights)` matrix for incoming connections.
- Per‑neuron overrides inside a layer:
  - `NeuronOverrideRange(start, end, ...)` applies to an inclusive index range
  - `NeuronOverride(index, ...)` applies to a single neuron
- Precedence: `NeuronOverride` (most specific) > `NeuronOverrideRange` > `BIUNetworkDefaults`.

### 🔌 DS interface (SDK parameters)
- `DSBitWidth` must be 4 or 8
- `DSClockMHz` must be positive
- `DSMode` defaults to `"ThresholdMode"` when not provided

### ⚡ Energy tables (optional)
- You can provide optional energy CSVs via the run configuration helpers.
- If they can’t be loaded, the simulator continues and energy lookups return 0.

### 🧭 Paths
- Examples are pre‑configured to work with the repository layout (simulator runs from `bin/Linux`).
- You typically won’t need to manage relative paths manually; the examples and helpers do it for you.

### 🚀 Examples (no arguments required)
- Minimal single‑neuron network: `python examples/build_minimal.py`
- Multilayer + override precedence: `python examples/build_multilayer_precedence.py`
- DS interface variants: `python examples/build_ds_variants.py`
- With energy tables: `python examples/build_with_energy_tables.py`

All examples define networks with the Python API, compile, and run the simulator automatically.

### ⚡ Quick Start (Python)

```python
from pathlib import Path
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile, build_run_config, write_text, write_json
from nemosdk.runner import NemoSimRunner

# 1) Define a minimal network
defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]

# 2) Compile (no XML editing required)
biu_xml, _ = compile(defaults, layers)

# 3) Write artifacts and run
out = Path("examples/out/quickstart")
biu_path = out / "biu.xml"
write_text(biu_path, biu_xml)
cfg = build_run_config(
    output_directory=out / "output",
    xml_config_path=biu_path,
    data_input_file=Path("tests/data/multi_layer_test/input.txt"),
    relativize_from=Path("bin/Linux"),
)
cfg_path = out / "config.json"
write_json(cfg_path, cfg)

runner = NemoSimRunner(working_dir=Path("bin/Linux"))
result = runner.run(cfg_path, check=True)
print("OK:", result.returncode)
```

Artifacts are written under `examples/out/...` and paths are relativized to `bin/Linux`.

### 📚 More documentation (advanced)
- Internal XML/config details are in `docs/BIUNetwork_Configuration.md` (you don’t need these for normal SDK usage).
- Release notes remain in `docs/WhatsNew.txt`.

---

### 🗂️ Table of Contents
- [✨ What it does](#-what-it-does)
- [📦 Install / Requirements](#-install--requirements)
- [🧰 Public API (import from nemosdk)](#-public-api-import-from-nemosdk)
- [🧩 BIU concepts & precedence](#-biu-concepts--precedence)
- [🔌 DS interface constraints](#-ds-interface-constraints)
- [⚡ Energy tables (optional configjson keys)](#-energy-tables-optional-configjson-keys)
- [🧭 Path resolution](#-path-resolution)
- [🚀 Examples (no arguments required)](#-examples-no-arguments-required)
- [📚 More documentation](#-more-documentation)
