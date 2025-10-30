## NemoSim XML Configuration (BIUNetwork)

This directory is the simulator working directory. The simulator expects an XML file that describes a BIU network and, optionally, a supervisor XML. Paths in `config.json` are typically resolved relative to this directory.

### Required root structure

```xml
<NetworkConfig type="BIUNetwork">
  <BIUNetwork>
    <!-- Global defaults (see below) -->
  </BIUNetwork>
  <Architecture>
    <Layer size="...">
      <synapses rows="R" cols="C">
        <weights>
          <row>...</row>
          <!-- R rows, each with exactly C numeric weights -->
        </weights>
      </synapses>
      <!-- Optional per‑neuron overrides (see below) -->
    </Layer>
    <!-- Add more <Layer> elements as needed -->
  </Architecture>
  <!-- Optional: additional elements depending on flow -->
  <!-- Optional: <Supervisor> parameters can be provided via a separate supervisor.xml -->
  <!-- The simulator ignores unknown elements. -->
  
  <!-- Optional convenience: input path hints, not always used by all flows -->
  <inputs>
    <data_file>../..//tests/data/multi_layer_test/input.txt</data_file>
  </inputs>
</NetworkConfig>
```

### Global BIU defaults (`<BIUNetwork>`) 

Supply any of the following. Missing values fall back to internal defaults or are overridden by per‑neuron settings.

- `VTh` (float, volts)
- `RLeak` (float, ohms)
- `refractory` (int, steps)
- `VDD` (float, volts)
- `Cn` (float, farads)
- `Cu` (float, farads)
- `fclk` (float, Hz)
- `DSBitWidth` (int: 4 or 8)
- `DSClockMHz` (float: > 0)
- `DSMode` (string: `ThresholdMode` or `FrequencyMode`; defaults to `ThresholdMode` if missing/empty)

Example:

```xml
<BIUNetwork>
  <VTh>0.6</VTh>
  <RLeak>5e8</RLeak>
  <refractory>12</refractory>
  <VDD>1.2</VDD>
  <Cn>1e-12</Cn>
  <Cu>4e-15</Cu>
  <fclk>1e7</fclk>
  <DSBitWidth>4</DSBitWidth>
  <DSClockMHz>10</DSClockMHz>
  <DSMode>ThresholdMode</DSMode>
  <!-- Optional: energy tables can be provided via config.json, not XML -->
</BIUNetwork>
```

### Architecture, synapses, and weights

- Each `Layer` must declare `size`.
- `<synapses rows="R" cols="C">` must match the weight matrix shape.
- `<weights>` must contain exactly `R` `<row>` elements; each `<row>` must have exactly `C` numbers.

Minimal 1×1 example:

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

Multi‑row example with overrides:

```xml
<Architecture>
  <Layer size="3">
    <synapses rows="3" cols="2">
      <weights>
        <row>1 2</row>
        <row>3 4</row>
        <row>5 6</row>
      </weights>
    </synapses>

    <!-- Optional per‑neuron overrides -->
    <NeuronRange start="0" end="2">
      <VTh>0.5</VTh>
      <RLeak>5.5e8</RLeak>
      <refractory>10</refractory>
    </NeuronRange>

    <!-- Most‑specific override wins over ranges -->
    <Neuron index="1">
      <VTh>0.7</VTh>
    </Neuron>
  </Layer>
</Architecture>
```

Override precedence: `Neuron` (single index) > `NeuronRange` > `<BIUNetwork>` defaults.

### Optional supervisor XML (analog defaults)

If your flow separates analog defaults, provide a separate file (commonly referenced by `config.json`):

```xml
<!-- supervisor.xml -->
<BIUNetwork>
  <fclk>1e7</fclk>
  <RLeak>1e6</RLeak>
  <VDD>1.2</VDD>
  <Cn>1e-12</Cn>
  <Cu>4e-15</Cu>
</BIUNetwork>
```

### Validation checklist

- Each `Layer` size equals `synapses rows`.
- Provide `<weights>`; do not omit it.
- Exactly `rows` `<row>` entries; each row has exactly `cols` numbers.
- Ranges: `0 ≤ start ≤ end < size`.
- Single indices: `0 ≤ index < size`.
- `DSBitWidth` ∈ {4, 8}; `DSClockMHz` > 0; `DSMode` defaults to `ThresholdMode` if missing.

### Notes

- Energy CSV paths (if used) are provided via `config.json` rather than XML.
- The simulator runs from this directory; relative paths in `config.json` are resolved from here.


