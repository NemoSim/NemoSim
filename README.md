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

### Top‑level structure

BIU networks are defined under a `NetworkConfig` root with `type="BIUNetwork"`, containing a global `BIUNetwork` section and an `Architecture` with one or more `Layer` elements.

```xml
<NetworkConfig type="BIUNetwork">
  <BIUNetwork>
    <!-- global defaults go here -->
  </BIUNetwork>
  <Architecture>
    <Layer size="...">
      <!-- synapses & optional per‑neuron overrides -->
    </Layer>
  </Architecture>
</NetworkConfig>
```

### Global BIU parameters (under `<BIUNetwork>`)

The following parameters define global defaults for the whole network. They can be overridden per layer/neurons as described below.

- `VTh` (double): Default neuron threshold voltage.
- `RLeak` (double): Default neuron leak resistance.
- `refractory` (int): Default refractory period (simulation timesteps).
- `VDD` (double): Supply voltage (used by energy/analog models).
- `Cn` (double): Neuron capacitance.
- `Cu` (double): Synapse/utility capacitance (as used by the model).
- `fclk` (double): Global clock frequency (Hz) used in some flows.
- `DSBitWidth` (int, 4 or 8): Downstream (DS) bit width for digital interface.
- `DSClockMHz` (double): DS clock in MHz. Must be positive.
- `DSMode` (string): `ThresholdMode` or `FrequencyMode`. If missing or empty, defaults to `ThresholdMode` (informational warning).

#### Parameter reference

| Name           | Type    | Units | Description |
|----------------|---------|-------|-------------|
| `VTh`          | double  | V     | Neuron threshold voltage (default). |
| `RLeak`        | double  | Ω     | Neuron leak resistance (default). |
| `refractory`   | int     | steps | Refractory period in simulation steps (default). |
| `VDD`          | double  | V     | Supply voltage for analog/energy models. |
| `Cn`           | double  | F     | Neuron capacitance. |
| `Cu`           | double  | F     | Synapse/aux capacitance used by the model. |
| `fclk`         | double  | Hz    | Global clock frequency used in some flows. |
| `DSBitWidth`   | int     | bits  | DS interface width; valid: 4 or 8. |
| `DSClockMHz`   | double  | MHz   | DS interface clock; must be positive. |
| `DSMode`       | string  | —     | `ThresholdMode` (default) or `FrequencyMode`. |

Notes from release notes (`docs/WhatsNew.txt`):
- If `DSMode` is missing/empty → default `ThresholdMode` is applied with an info/warning.
- `DSClockMHz` must be positive; otherwise a runtime error is raised.
- Existing elements still parsed: `fclk`, `VTh`, `RLeak`, `VDD`, `Cn`, `Cu`, `refractory`.

Example (condensed from `test2.xml`):

```xml
<BIUNetwork>
  <VTh>0.6</VTh>
  <RLeak>500e6</RLeak>
  <refractory>12</refractory>
  <DSClockMHz>10</DSClockMHz>
  <DSBitWidth>4</DSBitWidth>
  <DSMode>ThresholdMode</DSMode>
</BIUNetwork>
```

Supervisor defaults (analog parameters, `supervisor.xml`):

```xml
<BIUNetwork>
  <fclk>1e7</fclk>
  <RLeak>1e6</RLeak>
  <VDD>1.2</VDD>
  <Cn>1e-12</Cn>
  <Cu>4e-15</Cu>
</BIUNetwork>
```

### Architecture and synapses

Each `Layer` declares the number of neurons via `size`. Synapses are specified with a matrix shape and explicit weight rows:

- `synapses rows="R" cols="C"` declares the weight matrix shape for the layer.
- Inside `<weights>`, add `R` `<row>...</row>` elements, each with `C` numbers.

Minimal example (from `test.xml`):

```xml
<Architecture>
  <Layer size="1">
    <synapses rows="1" cols="1">
      <weights>
        <row>7.0</row>
      </weights>
    </synapses>
  </Layer>
</Architecture>
```

Multi‑row example (from `test2.xml`):

```xml
<Layer size="3">
  <synapses rows="3" cols="8">
    <weights>
      <row>6 5 5 5 5 -5 5 5</row>
      <row>5 -5 5 5 -5 5 5 5</row>
      <row>4 5 5 -5 5 5 5 5</row>
    </weights>
  </synapses>
  <!-- per‑neuron overrides can follow here -->
</Layer>
```

The release notes state weights are mandatory and must live under:

```xml
<synapses>
  <weights>
    <row>...</row>
  </weights>
</synapses>
```

Missing required `<weights>` or malformed `Layer size="..."` will produce errors.

### Per‑neuron configuration and precedence

Within each `Layer`, you can override the global defaults for subsets of neurons or individual neurons using two constructs. These affect at least the following scalars: `VTh`, `refractory`, `RLeak` (per release notes).

- `NeuronRange start="S" end="E"` sets values for an inclusive index range.
- `Neuron index="i"` sets values for one neuron.

Precedence (as shown by examples):
1. Per‑neuron (`<Neuron index="i">`) is most specific and takes precedence over ranges and global defaults.
2. Ranges (`<NeuronRange start="S" end="E">`) override global defaults for the covered indices.
3. Anything not explicitly overridden inherits from the `<BIUNetwork>` global.

Example: ranges plus single‑neuron tweak (from `test2.xml`):

```xml
<Layer size="7">
  <synapses rows="7" cols="3"> ... </synapses>

  <!-- First half [0..3] -->
  <NeuronRange start="0" end="3">
    <VTh>0.2</VTh>
  </NeuronRange>

  <!-- Second half [4..6] -->
  <NeuronRange start="4" end="6">
    <VTh>0.2</VTh>
    <RLeak>520e6</RLeak>
    <refractory>12</refractory>
  </NeuronRange>

  <!-- Most‑specific override for neuron 6 -->
  <Neuron index="6">
    <VTh>0.19</VTh>
  </Neuron>
</Layer>
```

Validation and errors (from `docs/WhatsNew.txt`):
- Invalid `NeuronRange` indices or malformed `Neuron index` produce errors.
- Missing required `<weights>` or `Layer size` issues produce errors.

### DS interface parameters

The BIU schema supports a simple downstream (digital) interface:

- `DSBitWidth`: accepted values are `4` or `8`.
- `DSClockMHz`: positive floating‑point clock frequency in MHz; required for successful runs.
- `DSMode`: `ThresholdMode` (default) or `FrequencyMode`.

If `DSMode` is missing or empty, the simulator applies `ThresholdMode` and emits an informational message. If `DSClockMHz` is missing or non‑positive, the simulator aborts with an error.

### Energy tables (optional, config file keys)

While not part of the XML itself, you can supply energy lookup CSVs via the run configuration (see `bin/Linux/Tests/SNN/BIU/config.json`):

- `synapses_energy_table_path`: CSV of synapse energy values.
- `neuron_energy_table_path`: CSV of neuron energy values.

Notes (from `docs/WhatsNew.txt`):
- Keys in the config file override any CSV paths that might appear elsewhere.
- Loading failures leave tables empty; energy lookups then return 0, without stopping the run.

Example `config.json` (fragment):

```json
{
  "output_directory": "./Tests/SNN/BIU/output_directory",
  "xml_config_path": "./Tests/SNN/BIU/test.xml",
  "sup_xml_config_path": "./Tests/SNN/BIU/supervisor.xml",
  "data_input_file": "./Tests/SNN/BIU/input.txt",
  "synapses_energy_table_path": "./Tests/SNN/BIU/Spike-in_vs_Not_spike-in.csv",
  "neuron_energy_table_path": "./Tests/SNN/BIU/Energy_Neuron_CSV_Content.csv"
}
```

### Quick checklist (from release notes)

- Provide correctly formatted CSVs with a header and at least one data row (if using energy tables).
- Ensure all paths are valid; relative paths resolve from the simulator’s working directory (`bin/Linux`).
- For per‑neuron overrides, keep ranges in bounds and provide well‑formed indices.
- Always include `<synapses><weights>...</weights></synapses>` inside each `Layer`.
- Set a positive `DSClockMHz`; `DSMode` defaults to `ThresholdMode` if omitted.

### Running the examples

From the project root, you can run the simulator using the helper script:

```bash
./scripts/run_nemosim.sh                          # default BIU example
./scripts/run_nemosim.sh bin/Linux/Tests/SNN/BIU  # directory (uses its config.json)
./scripts/run_nemosim.sh bin/Linux/Tests/SNN/BIU/config.json
```

Outputs are written to the path specified by `output_directory` in the corresponding `config.json`.

### Tests

- Test data lives under `tests/data/**` and each scenario contains its own `test.xml`, `supervisor.xml`, `input.txt`, CSVs, and an `output/` directory.
- Configs in `tests/data/**/config.json` use paths relative to the simulator working directory (`bin/Linux`). This is why the paths look like `../../tests/data/...`.
- Simulator outputs are ignored by git (see `.gitignore`).

Run the test suite:

```bash
cd tests
./run_tests.sh
```

### SDK (NemoSDK)

This repo includes a lightweight Python SDK to define → compile → run BIU networks.

- See `README_SDK.md` for API and concepts.
- Runnable examples live under `examples/` (no arguments needed):
  - `python examples/build_minimal.py`
  - `python examples/build_multilayer_precedence.py`
  - `python examples/build_ds_variants.py`
  - `python examples/build_with_energy_tables.py`
- Artifacts are written under `examples/out/...` and paths are relativized to `bin/Linux`.

Pinned assertions in the tests verify:
- Process success and end-of-run marker
- Exact total energy values for each scenario
- Sanity checks on generated outputs (spikes_/vin_/vns_ files exist, are non-empty, and have a minimum line count)
