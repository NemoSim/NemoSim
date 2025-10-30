## BIUNetwork configuration using the Python SDK

This document describes how to configure BIU spiking networks with the Python SDK (`nemosdk`). It replaces XML‑centric instructions with Python‑first examples for every parameter.

### Quick start (SDK)

```python
from pathlib import Path
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner

defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]

out_dir = Path("examples/out/sdk_quickstart")
config_path = compile_model(defaults=defaults, layers=layers, out_dir=out_dir, data_input_file=Path("tests/data/multi_layer_test/input.txt").resolve())

runner = NemoSimRunner(working_dir=Path("bin/Linux"))
result = runner.run(config_path, check=True)
```

Artifacts are written under `out_dir`. All paths in the generated `config.json` are absolute.

### Global network defaults: `BIUNetworkDefaults`

These are applied to all neurons unless overridden at the layer or per‑neuron level.

- VTh (float, volts): neuron threshold voltage.
- RLeak (float, ohms): leak resistance.
- refractory (int, steps): refractory period in simulation steps.
- VDD (float, volts): supply voltage (used in energy/analog models).
- Cn (float, farads): neuron capacitance.
- Cu (float, farads): synapse/aux capacitance.
- fclk (float, Hz): global clock (if relevant for your flow).
- DSBitWidth (int): DS interface width; must be 4 or 8.
- DSClockMHz (float): DS clock in MHz; must be > 0.
- DSMode (str): "ThresholdMode" (default) or "FrequencyMode".

Example:

```python
from nemosdk.model import BIUNetworkDefaults

defaults = BIUNetworkDefaults(
    VTh=0.6,
    RLeak=500e6,
    refractory=12,
    VDD=1.2,
    Cn=1e-12,
    Cu=4e-15,
    fclk=10e6,
    DSBitWidth=4,
    DSClockMHz=10,
    DSMode="ThresholdMode",
)
```

Validation rules enforced by the SDK:

- DSBitWidth ∈ {4, 8}; otherwise ValueError.
- DSClockMHz > 0; otherwise ValueError.
- DSMode defaults to "ThresholdMode" if not provided.

### Layers and synapses: `Layer` and `Synapses`

Each `Layer` declares its size and incoming synapses matrix. The synapse weight matrix must match `rows × cols` exactly.

```python
from nemosdk.model import Layer, Synapses

layer = Layer(
    size=3,
    synapses=Synapses(
        rows=3,
        cols=2,
        weights=[
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
        ],
    ),
)
```

Common validation errors:

- `size` must equal `rows`.
- `weights` must provide exactly `rows` lists, each with exactly `cols` numbers.

### Per‑neuron overrides and precedence

Override global defaults for ranges of neurons or individual neurons:

```python
from nemosdk.model import NeuronOverride, NeuronOverrideRange

layer = Layer(
    size=7,
    synapses=Synapses(rows=7, cols=3, weights=[[...],[...],[...],[...],[...],[...],[...]]),
    ranges=[
        NeuronOverrideRange(start=0, end=3, VTh=0.2),
        NeuronOverrideRange(start=4, end=6, VTh=0.2, RLeak=520e6, refractory=12),
    ],
    neurons=[
        NeuronOverride(index=6, VTh=0.19),
    ],
)
```

Precedence:

1) `NeuronOverride` (most specific)
2) `NeuronOverrideRange`
3) `BIUNetworkDefaults`

Validation errors:

- Range `start` ≤ `end` and both in `[0, size-1]`.
- Single `index` must be in `[0, size-1]`.

### DS interface configuration (SDK parameters)

```python
defaults = BIUNetworkDefaults(
    DSBitWidth=8,    # 4 or 8
    DSClockMHz=50,   # > 0
    DSMode="ThresholdMode",  # or "FrequencyMode"
)
```

If `DSMode` is omitted, it defaults to "ThresholdMode".

### Optional energy tables (run configuration)

Provide CSV tables via the run configuration helpers. If files are missing or out of range, lookups return 0 and the run continues.

```python
from nemosdk.compiler import build_run_config, write_json
from pathlib import Path

cfg = build_run_config(
    output_directory=Path("examples/out/energy/output"),
    xml_config_path=Path("examples/out/energy/biu.xml"),
    data_input_file=Path("tests/data/multi_layer_test/input.txt").resolve(),
    sup_xml_config_path=None,
)

# Inject optional energy CSVs
cfg["neuron_energy_table_path"] = str(Path("tests/data/multi_layer_test/Spike-in_vs_Not_spike-in.csv").resolve())
cfg["synapses_energy_table_path"] = str(Path("tests/data/multi_layer_test/Energy_Neuron_CSV_Content.csv").resolve())

write_json(Path("examples/out/energy/config.json"), cfg)
```

### Full example: compile and run

```python
from pathlib import Path
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner

defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]

out_dir = Path("examples/out/full")
config_path = compile_model(
    defaults=defaults,
    layers=layers,
    out_dir=out_dir,
    data_input_file=Path("tests/data/multi_layer_test/input.txt").resolve(),
)

runner = NemoSimRunner(working_dir=Path("bin/Linux"))
result = runner.run(config_path, check=True)
print("OK:", result.returncode)
```

### Notes

- All generated paths in `config.json` are absolute.
- Logs are captured under `bin/Linux/logs` when running via `NemoSimRunner`.
- See `README.md` for more examples and test instructions.
