## 🧠 NemoSDK · Lightweight Front‑End for NemoSim

Describe → Compile → Run BIU spiking networks using a clean Python API.

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
  - `Layer(size, synapses, ranges=[], neurons=[], probe=None)` — optional `probe` for easy data access
  - `Synapses(rows, cols, weights)`
  - `NeuronOverrideRange(start, end, VTh=?, RLeak=?, refractory=?)`
  - `NeuronOverride(index, VTh=?, RLeak=?, refractory=?)`
- Build & run helpers
  - `compile(defaults, layers, include_supervisor=False)` → compile
  - `build_run_config(...)` → internal runner config (usually used via examples/CLI)
  - `NemoSimRunner(working_dir).run(config_json_path)` → executes the simulator and captures logs
- Data access (probes)
  - `CompiledModel.get_probe(name)` → get LayerProbe for accessing simulation data
  - `CompiledModel.list_probes()` → list all available probe names
  - `LayerProbe.get_spikes(neuron_idx)` → get spike data for a neuron
  - `LayerProbe.get_vin(neuron_idx)` → get input voltage data
  - `LayerProbe.get_vns(neuron_idx)` → get neural state data
  - `LayerProbe.get_all_spikes()` → get all spikes for the layer
  - `LayerProbe.iter_spikes(neuron_idx, chunk_size=...)` → stream large outputs in chunks
  - `LayerProbe.to_dataframe(...)` → optional pandas helper for analysis/plotting
  - `LayerProbe.list_neuron_indices()` → discover available neuron ids
  - `watch_probe(probe, signal, neuron_idx, follow=True)` → tail output files in real time
- CLI (optional): `python -m nemosdk.cli` (`build`, `run`, `diag`, `probe`)

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
- With layer probes (easy data access): `python examples/build_with_probes.py`
- With plotting: `python examples/build_with_plotting.py`

All examples define networks with the Python API, compile, and run the simulator automatically.

### 🔍 Probe Workflow

1. **Name your layers** – assign `probe="input"` / `"hidden_0"` / `"output"` when constructing each `Layer`.
2. **Compile with `out_dir`** – the SDK emits `probes.json` alongside `config.json`, mapping probe names → layer metadata.
3. **Inspect results in Python**:

   ```python
   compiled = compile_model(..., out_dir=out_dir, data_input_file=input_file)
   probe = compiled.get_probe("output")

   # Whole-layer helpers
   spikes = probe.get_all_spikes()              # {neuron_idx: [0/1, ...]}
   chunks = list(probe.iter_spikes(0, chunk_size=2048))  # stream large files

   # Pandas integration (optional dependency)
   df = probe.to_dataframe(neurons=[0, 1], signals=("spikes", "vin"))

   # Quick summaries
   print(probe.list_neuron_indices())  # [0, 1, 2, ...]
   ```

4. **Tail results during a run** – `watch_probe(probe, "spikes", 0, follow=True)` yields live samples.
5. **Use the CLI for ad-hoc inspection** – `python -m nemosdk.cli probe config.json --list` or `--probe output --signal vin --head 10`.

### ⚡ Quick Start (Python)

```python
from pathlib import Path
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner

# 1) Define a minimal network with optional probe
defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]), probe="output")]

# 2) Two lines: compile, then run
out = Path("examples/out/quickstart")
compiled = compile_model(
    defaults=defaults,
    layers=layers,
    out_dir=out,
    data_input_file=(Path("tests/data/multi_layer_test/input.txt")).resolve(),
)

result = NemoSimRunner(working_dir=Path("bin/Linux")).run(compiled, check=True)
print("OK:", result.returncode)

# 3) Access simulation data by probe name (no manual file handling!)
probe = compiled.get_probe("output")
spikes = probe.get_spikes(0)  # Get spikes for neuron 0
print(f"Neuron 0 fired {sum(spikes)} times")

# Optional: Override binary path via environment variable or explicit parameter
# export NEMOSIM_BINARY=/custom/path/to/nemosim
# Or: NemoSimRunner(working_dir=Path("bin/Linux"), binary_path=Path("/custom/path"))
```

💡 Need tabular analysis? Install pandas and call `probe.to_dataframe(...)` to obtain a tidy DataFrame for plotting or notebooks.

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

### 🔧 Environment & Installation

- Supported: Python ≥ 3.10; Linux (tested)
- Install with uv:
  - `curl -Ls https://astral.sh/uv/install.sh | sh`
  - `uv venv .venv`
  - `uv pip install -e .`
- Or with pip:
  - `python3 -m pip install -e .`

### 🧪 Testing & Development

- Run SDK tests: `uv run -q pytest -q tests/sdk` (or `python3 -m pytest -q tests/sdk`)
- Code style: fully typed public API; prefer small, cohesive modules

### 🏃 Simulator Expectations

- Binary must exist at `bin/Linux/NEMOSIM` (default) or as specified
- Use `NemoSimRunner(working_dir=Path("bin/Linux"))`
- Binary path resolution priority:
  1. Explicit `binary_path` parameter (if provided)
  2. `NEMOSIM_BINARY` environment variable (if set)
  3. Default: `working_dir / "NEMOSIM"`
- Logs are captured under `bin/Linux/logs`

**Example: Using environment variable to override binary path:**
```bash
export NEMOSIM_BINARY=/path/to/custom/nemosim
python your_script.py
```

### 📁 Paths Policy

- All paths in the generated `config.json` are absolute
- Pass `data_input_file` as an absolute path

### 🧰 Two‑Line Flow Recap

1) `compiled = compile(defaults, layers, out_dir=..., data_input_file=...)`
2) `NemoSimRunner(working_dir=Path("bin/Linux")).run(compiled)`

### 🛠️ Troubleshooting

- Missing or non‑executable simulator: `chmod +x bin/Linux/NEMOSIM`
- Non‑zero exit: check the latest logs in `bin/Linux/logs`
- DS constraints: ensure `DSBitWidth ∈ {4,8}` and `DSClockMHz > 0`

### 🌐 Project Site

- Background and objectives: `https://nemo.org.il/`

### 🤝 Contributing

- PRs welcome (typed APIs, tests, docs). License: MIT
