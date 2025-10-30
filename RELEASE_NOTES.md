## NemoSim / NemoSDK Release Notes

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


