## NemoSim / NemoSDK Release Notes

### v0.2.2 (Alpha) — 2025-11-15

Status: Alpha. Supervisor defaults are now hard-coded; main network defaults remain user-configurable.

#### Changed
- **Supervisor defaults are now hard-coded**: The `supervisor_defaults` parameter has been removed from all compile functions
  - Supervisor XML now always uses hard-coded defaults: `fclk=1e7`, `RLeak=1e6`, `VDD=1.2`, `Cn=1e-12`, `Cu=4e-15`
  - Main `BIUNetworkDefaults` remain fully user-configurable
  - This simplifies the API and ensures consistent supervisor configuration across all models
- Updated all examples to remove `supervisor_defaults` parameter usage
- Updated CLI: removed supervisor defaults arguments (main defaults arguments remain)
- Updated documentation (README.md) to clarify supervisor defaults are hard-coded

#### Removed
- `supervisor_defaults` parameter from `compile_to_xml()`, `compile()`, and `compile_and_write()` functions
- Supervisor defaults CLI arguments (main defaults CLI arguments remain available)

#### Repository Hygiene
- Updated `.gitignore` to ignore all log files (`*.log` and `**/logs/` patterns)
- Removed all existing log files from the repository

#### Migration Guide
If you were using `supervisor_defaults`:
```python
# Before (v0.2.1)
compiled = compile(
    defaults=defaults,
    layers=layers,
    include_supervisor=True,
    supervisor_defaults=supervisor_defaults,  # ❌ No longer supported
)

# After (v0.2.2)
compiled = compile(
    defaults=defaults,  # ✅ Main defaults still configurable
    layers=layers,
    include_supervisor=True,  # ✅ Supervisor uses hard-coded defaults
)
```

#### Notes
- This is a **breaking change** for code that explicitly set `supervisor_defaults`
- Main network defaults (`BIUNetworkDefaults`) are unaffected and remain fully configurable
- All examples and tests have been updated to reflect this change
- Supervisor defaults are optimized for typical use cases and cannot be customized

### v0.2.1 (Alpha) — 2025-11-09

Status: Alpha. Example improvements to guarantee spiking activity and added regression tests.

#### Added
- Inline input example now ships with supervisor parameters and lower threshold so neurons fire without manual tuning (`examples/build_with_inline_input.py`)
- Probe example updated to include supervisor defaults for consistent output files (`examples/build_with_probes.py`)
- Integration tests covering both examples to guard regression (`tests/sdk/test_examples.py`)
- Release notes updated to document the inline input workflow

#### Changed
- No API changes; examples now reuse shared hyperparameters to ensure generated artifacts contain spikes
- Documentation refreshed to mention the inline-input tuning

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
- Advanced probe helpers:
  - `LayerProbe.iter_spikes/iter_vin/iter_vns` for chunked streaming
  - `LayerProbe.to_dataframe(...)` (optional pandas dependency) for notebook/table workflows
  - `LayerProbe.list_neuron_indices()` to discover available neuron ids
- Real-time monitoring via `watch_probe(probe, signal, neuron_idx, follow=True)`
- Artifact metadata: `probes.json` is emitted next to `config.json` with probe → layer mappings
- CLI: new `nemosdk probe` subcommand (`--list`, `--probe`, `--signal`, `--head`, `--follow`, `--max-events`) for quick terminal inspection
- Provide input data programmatically via `input_data=[...]` (SDK writes `input.txt` automatically)
- New example `examples/build_with_inline_input.py` demonstrating inline stimulus use
- Comprehensive test suite for probe functionality (`tests/sdk/test_probes.py`)
- Dedicated CLI probe tests (`tests/sdk/test_cli_probe.py`)
- Example demonstrating probe usage (`examples/build_with_probes.py`)

#### Changed
- Probe names must be unique across all layers (validated at compile time)
- Enhanced error messages for missing probe names and files
- Documentation updates covering probe workflow, CLI usage, pandas integration, and best practices (README + `docs/BIUNetwork_Configuration.md`)

#### Benefits
- No need to manually construct output file paths or track layer indices
- Clean API for accessing simulation results: `compiled.get_probe("layer_name").get_spikes(0)`
- Rich analysis tooling: chunked streaming, DataFrame export, CLI inspection, and live tailing via `watch_probe`
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


