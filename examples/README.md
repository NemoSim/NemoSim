# NemoSDK Examples

This directory contains runnable examples demonstrating common tasks:

- Minimal 1×1 network (matches `bin/Linux/Tests/SNN/BIU/test.xml` semantics)
- Multilayer with per-neuron precedence (ranges vs. index)
- DS interface variants (defaulted DSMode, FrequencyMode)
- Config with optional energy tables
- Results plotting and visualization

### Usage

From repo root:

```bash
python examples/build_minimal.py                    # builds and runs
python examples/build_multilayer_precedence.py
python examples/build_ds_variants.py
python examples/build_with_energy_tables.py
python examples/build_with_plotting.py              # builds, runs, and plots results
python examples/build_with_probes.py                # builds, runs, inspects probes
python examples/build_with_inline_input.py          # builds, runs, inline stimulus

# Or run all
bash examples/run_all.sh
```

Note: `build_with_plotting.py` requires `matplotlib` and `numpy`:

```bash
pip install matplotlib numpy
```

Artifacts are written under `examples/out/<scenario>/`:

- `biu.xml` (+ optional `supervisor.xml`)
- `config.json` (uses absolute paths)
- `output/` (created by NemoSim when `--run` is used)

Notes:

- NemoSim runs from `bin/Linux`; ensure `bin/Linux/NEMOSIM` exists and is executable.


