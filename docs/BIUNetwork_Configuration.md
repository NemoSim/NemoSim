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

**Providing input data directly:**

```python
input_samples = [0, 1, 0, 1]

config_path = compile_model(
    defaults=defaults,
    layers=layers,
    out_dir=out_dir,
    input_data=input_samples,  # writes input.txt automatically
)
```

`input_data` is only supported when `out_dir` is supplied; the SDK writes `input.txt` into the output directory and references it from the generated `config.json`.

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
    probe="layer_name",  # Optional: assign a name for easy data access
)
```

Common validation errors:

- `size` must equal `rows`.
- `weights` must provide exactly `rows` lists, each with exactly `cols` numbers.

### Layer Probes (optional)

Assign an optional `probe` name to layers to easily access their output data after simulation without manually tracking layer indices or opening files.

```python
# Define layers with probes
input_layer = Layer(
    size=3,
    synapses=Synapses(rows=3, cols=8, weights=[[...]]),
    probe="input",  # Name this layer "input"
)

output_layer = Layer(
    size=7,
    synapses=Synapses(rows=7, cols=3, weights=[[...]]),
    probe="output",  # Name this layer "output"
)

# Compile the model
compiled = compile_model(
    defaults=defaults,
    layers=[input_layer, output_layer],
    out_dir=out_dir,
    data_input_file=data_file,
)

# After running the simulation
runner = NemoSimRunner(working_dir=Path("bin/Linux"))
runner.run(compiled, check=True)

# Access data by probe name (no need to remember layer indices!)
input_probe = compiled.get_probe("input")
output_probe = compiled.get_probe("output")

# Get data for specific neurons
spikes_0 = input_probe.get_spikes(0)  # Spike data for neuron 0
vin_0 = output_probe.get_vin(0)       # Input voltage for neuron 0
vns_0 = output_probe.get_vns(0)       # Neural state for neuron 0

# Get data for all neurons in a layer
all_spikes = output_probe.get_all_spikes()  # Dict[neuron_idx, List[spike_values]]
all_vin = output_probe.get_all_vin()        # Dict[neuron_idx, List[voltage_values]]
all_vns = output_probe.get_all_vns()        # Dict[neuron_idx, List[state_values]]

# List available probes
available = compiled.list_probes()  # ["input", "output"]
```

Probe features:

- **Optional**: Layers without probes work as before
- **Unique names**: Each probe name must be unique across all layers (validated at compile time)
- **Easy data access**: No need to construct file paths like `spikes_{layer_idx}_{neuron_idx}.txt`
- **Type safety**: Returns properly typed data (int for spikes, float for voltages)
- **Error handling**: Clear error messages if probe name doesn't exist or output files are missing

Benefits:

- Makes post-simulation analysis cleaner and more readable
- Reduces errors from incorrect layer indices or file paths
- Self-documenting: probe names describe what each layer represents

#### Probe best practices

- Use descriptive names per layer (e.g., `"input"`, `"hidden_1"`, `"output"`) to make analysis code self-explanatory.
- `compile(..., out_dir=...)` automatically emits `probes.json` alongside `config.json`. This file maps probe names to layer indices/sizes for tooling such as the CLI.
- Stream large outputs without loading everything at once:

  ```python
  for chunk in probe.iter_spikes(0, chunk_size=2048):
      process(chunk)
  ```

- Need tabular data? Install pandas (`pip install pandas`) and call `probe.to_dataframe(...)` to obtain a tidy DataFrame ready for plotting.
- Want quick, ad-hoc inspection? Use the CLI: `python -m nemosdk.cli probe config.json --probe output --signal vns --head 5`.
- Monitor simulations in real time with `watch_probe(probe, "spikes", 0, follow=True)`, which tails the underlying output files.

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
- Probe metadata is stored in `probes.json` alongside `config.json`; `CompiledModel` loads it automatically for the probe API and CLI tooling.
