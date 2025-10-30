## NemoSDK (lightweight front-end for NemoSim)

Describe → Compile → Run BIU spiking networks as XML/JSON artifacts accepted by NemoSim.

### What it does
- Define BIU networks layer-by-layer with optional per-neuron overrides.
- Validate shapes, DS interface constraints, and precedence rules.
- Emit BIU XML and optional supervisor XML.
- Create `config.json` aligned with repository examples and `docs/WhatsNew.txt`.
- Run NemoSim with logs captured to files.

### Install / Requirements
- Python ≥ 3.10, stdlib only (numpy optional, not required).

### Public API (import from `nemosdk`)
- Model: `BIUNetworkDefaults`, `Layer`, `Synapses`, `NeuronOverrideRange`, `NeuronOverride`.
- Compiler: `compile_to_xml(defaults, layers, include_supervisor=False)`, `build_run_config(...)`.
- Runner: `NemoSimRunner(working_dir, binary_path=None).run(config_json, extra_args=None, logs_dir=None)`.
- CLI: `python -m nemosdk.cli` (subcommands: `build`, `run`, `diag`).

### BIU concepts & precedence
- Global defaults live under `<BIUNetwork>`.
- Per-layer overrides (within `<Layer>`):
  - `NeuronRange start..end` and `Neuron index` support `VTh`, `RLeak`, `refractory`.
- Precedence: Neuron index > NeuronRange > global defaults.

### DS interface constraints
- `DSBitWidth ∈ {4, 8}`.
- `DSClockMHz > 0`.
- `DSMode`: if missing/empty → defaults to `ThresholdMode` (informational).

### Energy tables (optional config.json keys)
- `synapses_energy_table_path`, `neuron_energy_table_path` override other sources.
- Loading failures are non-fatal; energy lookups return 0 (simulator behavior).

### Path resolution
- NemoSim resolves relative paths from its working directory (examples use `bin/Linux`).
- `build_run_config(..., relativize_from=Path('bin/Linux'))` helps ensure configs work with the helper script.

### CLI Examples
- Build minimal artifacts:
  - `python -m nemosdk.cli build out_dir tests/data/multi_layer_test/input.txt --sim-workdir bin/Linux --include-supervisor`
- Run simulator:
  - `python -m nemosdk.cli run out_dir/config.json --sim-workdir bin/Linux`
- Diagnose how a path resolves for NemoSim:
  - `python -m nemosdk.cli diag --sim-workdir bin/Linux tests/data/multi_layer_test/config.json`

### Gotchas
- Ensure each `Layer` has `<synapses><weights>...</weights></synapses>` with `rows` rows and `cols` columns per row; rows must equal layer size.
- Keep `NeuronRange` in-bounds and `Neuron index` within layer size.
- Provide a positive `DSClockMHz`; missing/invalid values cause errors.
- If CSVs are missing/unreadable, runs continue but energy totals may be 0.


