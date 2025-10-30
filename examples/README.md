## NemoSDK Examples

This directory contains runnable examples demonstrating common tasks:

- Minimal 1×1 network (matches `bin/Linux/Tests/SNN/BIU/test.xml` semantics)
- Multilayer with per-neuron precedence (ranges vs. index)
- DS interface variants (defaulted DSMode, FrequencyMode)
- Config with optional energy tables

### Usage

From repo root:

```bash
python examples/build_minimal.py --run              # builds and runs
python examples/build_multilayer_precedence.py --run
python examples/build_ds_variants.py --run
python examples/build_with_energy_tables.py --run

# Or run all
bash examples/run_all.sh
```

Artifacts are written under `examples/out/<scenario>/`:
- `biu.xml` (+ optional `supervisor.xml`)
- `config.json` (paths relative to `bin/Linux`)
- `output/` (created by NemoSim when `--run` is used)

Notes:
- NemoSim resolves relative paths from `bin/Linux`. These examples set `relativize_from='bin/Linux'` so they work with the repo’s simulator layout.
- `--run` requires `bin/Linux/NEMOSIM` to exist and be executable.


