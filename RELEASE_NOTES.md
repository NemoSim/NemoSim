## NemoSim / NemoSDK Release Notes

### v0.2.0 (Alpha) — 2025-11-07

Status: Alpha. New probe feature for easy data access; backward compatible with existing code.

#### Added
- **Layer Probes**: Optional probe names for layers to access simulation data without manual file handling
  - New `probe` field on `Layer` class (optional string)
  - `LayerProbe` class for reading layer output data by probe name
  - `CompiledModel.get_probe(name)` to access layer data after simulation
  - `CompiledModel.list_probes()` to list all available probes
  - Methods on `LayerProbe`:
    - `get_spikes(neuron_idx)` - Get spike data for a specific neuron
    - `get_vin(neuron_idx)` - Get synapse input voltage data
    - `get_vns(neuron_idx)` - Get neural state potential data
    - `get_all_spikes()` - Get spike data for all neurons in the layer
    - `get_all_vin()` - Get input voltage data for all neurons
    - `get_all_vns()` - Get neural state data for all neurons
- Comprehensive test suite for probe functionality (`tests/sdk/test_probes.py`)
- Example demonstrating probe usage (`examples/build_with_probes.py`)

#### Changed
- Probe names must be unique across all layers (validated at compile time)
- Enhanced error messages for missing probe names and files

#### Benefits
- No need to manually construct output file paths or track layer indices
- Clean API for accessing simulation results: `compiled.get_probe("layer_name").get_spikes(0)`
- Backward compatible: probes are optional; existing code works unchanged

#### Example Usage
```python
# Define layers with probes
layer0 = Layer(size=3, synapses=Synapses(...), probe="input")
layer1 = Layer(size=7, synapses=Synapses(...), probe="output")

# Compile and run
compiled = compile(defaults, [layer0, layer1], out_dir=out_dir, ...)
runner.run(compiled)

# Access data by probe name
input_probe = compiled.get_probe("input")
spikes = input_probe.get_spikes(0)  # Get spikes for neuron 0
all_spikes = input_probe.get_all_spikes()  # Get all spikes for the layer
```

### v0.1.1 (Alpha) — 2025-10-30

Status: Alpha. Developer‑experience updates; no breaking runtime changes expected.

#### Changed
- Consolidated tests under a single `tests/` folder:
  - SDK tests moved to `tests/sdk/` (removed `tests_sdk/`)
  - Simulator tests moved to `tests/sim/` with unchanged data under `tests/data/`
  - Updated scripts: `tests/run_tests_sdk.sh` and `tests/run_tests.sh`
- Documentation refresh:
  - `docs/BIUNetwork_Configuration.md` rewritten to be SDK‑only with parameter examples
  - Added `bin/Linux/README.md` describing the exact expected XML structure
- Code comments & CLI polish:
  - Added docstrings across `nemosdk/model.py`, `compiler.py`, `runner.py`, `cli.py`
  - Minor CLI fix to use `CompiledModel` when running

#### Removed / Repo Hygiene
- Removed DS lookup tables from VCS and added ignores:
  - Deleted `bin/Linux/DS_0`–`DS_7`; added to `.gitignore` (also covers `bin/Linux/DS_tables/`)
  - All simulator tests still pass without these files present in the repo
- Ignored simulator logs: added `bin/Linux/logs/` to `.gitignore` and cleaned existing logs

#### Notes
- No public SDK API changes; compile→run flows and examples are unaffected.
- If your deployment requires DS tables, ensure they are provided at runtime alongside `NEMOSIM`.

### v0.1.0 (Alpha) — 2025-10-30

Status: Alpha. Linux-only. Public APIs may change.

#### Added
- BIU network DS interface parameters in XML and SDK:
  - `DSBitWidth` (4 or 8), `DSClockMHz` (>0), `DSMode` (ThresholdMode | FrequencyMode).
- Per‑neuron scalar overrides at the layer level:
  - `NeuronOverrideRange(start, end, VTh?, RLeak?, refractory?)`
  - `NeuronOverride(index, VTh?, RLeak?, refractory?)`
  - Precedence: Neuron > Range > Global defaults.
- Mandatory synapse weight structure validation (`<synapses><weights><row>...</row></weights></synapses>`).
- Optional energy table support via run configuration keys:
  - `neuron_energy_table_path`, `synapses_energy_table_path` (CSV lookups; out‑of‑range → 0).
- Python SDK (`nemosdk`) with clean model/compile/run API and CLI entry point:
  - `compile(...)` to generate simulator artifacts
  - `NemoSimRunner(...).run(config_json_path)` to execute `bin/Linux/NEMOSIM`
  - CLI: `nemosdk` (build/run/diag)
- Examples that build and run end‑to‑end (outputs under `examples/out/...`):
  - Minimal, multilayer precedence, DS variants, and energy tables.

#### Changed / Enforcement
- Stricter validation and fallback behaviors:
  - Missing `DSMode` defaults to `ThresholdMode` (info log); empty value → warning + default.
  - Invalid neuron indices and malformed ranges produce errors.
  - Missing `<weights>` or inconsistent layer sizes produce errors.

#### Developer Notes
- All generated paths in `config.json` are absolute; examples relativize execution to `bin/Linux`.
- Energy CSV parsing tolerates missing files by yielding zero lookups (non‑fatal at parse stage).
- Logs are captured under `bin/Linux/logs` when running via the SDK.

#### Known Limitations
- Linux‑only simulator binary expected at `bin/Linux/NEMOSIM`.
- Alpha quality: APIs and file formats may evolve.

#### References
- BIU/DS XML and config details: `docs/BIUNetwork_Configuration.md`
- What’s New (source details): `docs/WhatsNew.txt`
- Examples: `examples/`


