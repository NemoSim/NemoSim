## BIUNetwork configuration guide (NemoSim)

This guide explains how to configure a BIU spiking network and per‑neuron parameters using the XML schema used by NemoSim. All examples and parameter descriptions are derived from the files in this repository.

### Relevant examples in this repo

- BIU example with ranges and per‑neuron overrides: `bin/Linux/Tests/SNN/BIU/test2.xml`
- Minimal BIU network: `bin/Linux/Tests/SNN/BIU/test.xml`
- BIU supervisor defaults (global analog params): `bin/Linux/Tests/SNN/BIU/supervisor.xml`
- Release notes for new fields and behavior: `bin/WhatsNew.txt`

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

Notes from release notes (`bin/WhatsNew.txt`):
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

Validation and errors (from `bin/WhatsNew.txt`):
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

Notes (from `bin/WhatsNew.txt`):
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
./run_nemosim.sh                               # default BIU example
./run_nemosim.sh bin/Linux/Tests/SNN/BIU       # directory (uses its config.json)
./run_nemosim.sh bin/Linux/Tests/SNN/BIU/config.json
```

Outputs are written to the path specified by `output_directory` in the corresponding `config.json`.


