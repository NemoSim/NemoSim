# NemoSim User Guide

**Nemo Project**  
**NemoSim Simulator Tool**  
**User Guide**  
**Rev. 1.2**  
**August 2025**

---

## Documentation Control

### History Table

| Version | Date | Description | Author/Remarks |
|---------|------|-------------|----------------|
| 1.0 | 31 July 2025 | Initial release | Marika Klubakov |
| 1.1 | 7 August 2025 | Revised and expanded | Marika Klubakov |
| 1.2 | 19 August 2025 | In Section 2.1: Updated and explained the LIF and BIU network XML codes. Added a note about the optional LIF YFlash field. In Section 2.2, added a note about the optional BIU sup_xml_config_path field. In Section 2.4, reformatted the filename syntax. In Section 3, added an important note. | Ibrahem Saed Ahmd |

### Approval Table

| Version | Date | Full Name | Title | Signature |
|---------|------|-----------|-------|-----------|
| 1.0 | 31/7/25 | Marika Klubakov | Marika Klubakov | |
| 1.1 | 7/8/25 | Marika Klubakov | Marika Klubakov | |
| 1.2 | 19/8/25 | Marika Klubakov | Marika Klubakov | |

---

## Disclaimer and Proprietary Information Notice

The information contained in this document does not represent a commitment on any part by Ceva, Inc., or its subsidiaries (collectively, "Ceva"). Ceva makes no warranty of any kind with regard to this material, including, but not limited to implied warranties of merchantability and fitness for a particular purpose whether arising out of law, custom, conduct, or otherwise.

Additionally, Ceva assumes no responsibility for any errors or omissions contained herein, and assumes no liability for special, direct, indirect, or consequential damage, losses, costs, charges, claims, demands, fees, or expenses, of any nature or kind, which are incurred in connection with the furnishing, performance, or use of this material.

This document contains proprietary information, which is protected by U.S. and international copyright laws. All rights reserved. No part of this document may be reproduced, photocopied, or translated into another language without the prior written consent of Ceva. CEVA® is a registered name of Ceva. All product names are trademarks of Ceva, or of its applicable suppliers if so stated.

---

## Support

Ceva makes great efforts to provide a user-friendly software and hardware development environment. Along with this, Ceva provides comprehensive documentation, enabling users to learn and develop applications on their own. Due to the complexities involved in the development of DSP applications that might be beyond the scope of the documentation, an online Technical Support Service has been established. This service includes useful tips and provides fast and efficient help, assisting users to quickly resolve development problems.

### How to Get Technical Support

- **FAQs**: Visit our website http://www.ceva-ip.com or your company's protected page on the Ceva website for the latest answers to frequently asked questions.
- **Application Notes**: Visit our website http://www.ceva-ip.com or your company's protected page on the Ceva website for the latest application notes.
- **Email**: Use the Ceva central support email address ceva-support@ceva-ip.com. Your email will be forwarded automatically to the relevant support engineers and tools developers who will provide you with the most professional support to help you resolve any problem.
- **License Keys**: Refer any license key requests or problems to sdtkeys@ceva-ip.com. For SDT license keys installation information, see the SDT Installation and Licensing Scheme Guide.

**Email**: ceva-support@ceva-ip.com  
**Visit us at**: www.ceva-ip.com

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Overview](#11-overview)
   - 1.2 [Purpose](#12-purpose)
   - 1.3 [Key Features](#13-key-features)
   - 1.4 [Typical Use Cases](#14-typical-use-cases)
2. [What's New](#2-whats-new)
   - 2.1 [BIU Network Additions](#21-biu-network-additions)
   - 2.2 [Per-Neuron Overrides (BIU)](#22-per-neuron-overrides-biu)
   - 2.3 [Mandatory Synapse Weight Structure](#23-mandatory-synapse-weight-structure)
   - 2.4 [Fallback / Validation Messages](#24-fallback--validation-messages)
   - 2.5 [BIU Configuration Example](#25-biu-configuration-example)
   - 2.6 [New Config File Keys](#26-new-config-file-keys)
   - 2.7 [CSV Input Formats](#27-csv-input-formats)
   - 2.8 [Parser Behavior](#28-parser-behavior)
   - 2.9 [Exposed Outputs](#29-exposed-outputs)
   - 2.10 [Validation & Fallback](#210-validation--fallback)
   - 2.11 [Practical Checklist](#211-practical-checklist)
   - 2.12 [Summary](#212-summary)
3. [Using the NemoSim Simulation Tool](#3-using-the-nemosim-simulation-tool)
   - 3.1 [Step 1: Preparing the XML/TXT Files](#31-step-1-preparing-the-xmltxt-files)
   - 3.2 [Step 2: Preparing the JSON File](#32-step-2-preparing-the-json-file)
   - 3.3 [Step 3: Running the NemoSim Simulator Tool](#33-step-3-running-the-nemosim-simulator-tool)
   - 3.4 [Step 4: Plotting the Outputs](#34-step-4-plotting-the-outputs)
4. [Error Handling](#4-error-handling)
   - 4.1 [Error Message Formats](#41-error-message-formats)
   - 4.2 [Possible Return Codes](#42-possible-return-codes)
5. [References](#5-references)

---

# 1. Introduction

## 1.1 Overview

This document describes the NemoSim simulation tool, which is used for spiking neural network architectures, and has been developed as part of the Nemo Project.

It enables researchers and engineers to model, simulate, and analyze the behavior of various neural network types, such as Leaky Integrate-and-Fire (LIF) and Brain-Inspired Unit (BIU) networks.

## 1.2 Purpose

NemoSim is designed to:

- Simulate neural network architectures using user-defined configurations
- Model time-evolving neuron and synapse states in response to input currents
- Support both standard and custom network types (LIF, BIU, and extensible for new models)
- Generate outputs for scientific analysis and visualization, including detailed time-series data for neural state, synapse activity, and spikes
- Facilitate debugging and research, with outputs and tools to identify and analyze network behavior

## 1.3 Key Features

- **Flexible Input**: NemoSim accepts XML-based network descriptions and plain text current input files, supporting both manual and scripted generation.
- **Extensible Design**: The modular codebase allows for easy addition of new neuron/synapse models and architectures.
- **Comprehensive Output**: The tool produces multiple output files (membrane potentials, synaptic inputs, spikes, and so on) for analysis and plotting.
- **Analysis Tools**: NemoSim includes Python scripts and guidelines for visualizing and interpreting simulation results.
- **Robust Error Handling**: The tool detects and reports errors in input files and configuration, aiding reproducibility.

## 1.4 Typical Use Cases

- Computational neuroscience research
- Neuromorphic hardware prototyping and validation
- Algorithm development and prototyping for spiking neural networks

---

# 2. What's New

This section describes the latest updates and new features added to NemoSim.

## 2.1 BIU Network Additions

New child elements under `<BIUNetwork>`:

- `<DSBitWidth>` (int: 4/8) → NetworkParameters.DSBitWidth
- `<DSClockMHz>` (double) → NetworkParameters.DSClockMHz
- `<DSMode>` (string: ThresholdMode | FrequencyMode) → NetworkParameters.DSMode

Existing BIU elements still parsed:

- `<fclk>`, `<VTh>`, `<RLeak>`, `<VDD>`, `<Cn>`, `<Cu>`, `<refractory>`

## 2.2 Per-Neuron Overrides (BIU)

Inside each `<Layer>`:

- Optional repeated `<NeuronRange start="S" end="E">` with any of:
  - `<VTh>`, `<refractory>`, `<RLeak>`
- Optional repeated `<Neuron index="i">` with any of:
  - `<VTh>`, `<refractory>`, `<RLeak>`

These populate per-layer vectors:

- `biuNeuronVTh[layer]`, `biuNeuronRefractory[layer]`, `biuNeuronRLeak[layer]`

## 2.3 Mandatory Synapse Weight Structure

Each `<Layer>` must contain:

```xml
<synapses>
  <weights>
    <row>...</row>
    ...
  </weights>
</synapses>
```

## 2.4 Fallback / Validation Messages

- Missing `<DSMode>` → defaults to `ThresholdMode` (informational log).
- Empty `<DSMode>` element → warning, default applied.
- Invalid `<NeuronRange>` indices or malformed `<Neuron index>` produce errors.
- Missing required `<weights>` or `<Layer size="...">` produce errors.

## 2.5 BIU Configuration Example

BIU with DS & per-neuron overrides:

```xml
<NetworkConfig type="BIUNetwork">
  <BIUNetwork>
    <VDD>1.0</VDD>
    <VTh>0.25</VTh>
    <RLeak>0.001</RLeak>
    <Cn>1e-12</Cn>
    <Cu>1e-12</Cu>
    <refractory>5</refractory>
    <DSBitWidth>8</DSBitWidth>
    <DSClockMHz>50</DSClockMHz>
    <DSMode>ThresholdMode</DSMode>
  </BIUNetwork>
  <Architecture>
    <Layer size="4">
      <NeuronRange start="0" end="1"><VTh>0.3</VTh></NeuronRange>
      <Neuron index="2"><refractory>7</refractory></Neuron>
      <synapses>
        <weights>
          <row>0.1 0.2 0.3 0.4</row>
          <row>0.0 0.1 0.0 0.2</row>
          <row>0.5 0.4 0.3 0.2</row>
          <row>0.2 0.1 0.2 0.1</row>
        </weights>
      </synapses>
    </Layer>
  </Architecture>
</NetworkConfig>
```

## 2.6 New Config File Keys

Added (or now actively used) colon-separated entries in the text config (not JSON) to direct the parser:

- `neuron_energy_table_path`: Path to neuron energy CSV.
- `synapses_energy_table_path`: Path to synapse energy CSV.

These are read by `parseConfigFromFile` and copied into `NetworkParameters` (overriding XML values if present).

## 2.7 CSV Input Formats

Both tables share a simple row-oriented CSV structure:

- First line: header (ignored).
- Each data line: first column is a label (ignored), remaining columns are numeric energy values.

**Synapse energy table:**

- Interpreted as energy per (weight class, spike-rate class).
- Accessed using 1-based indices; out-of-range queries yield 0.
- Weight classes correspond to integerized weight values.
- Spike-rate classes correspond to integer rate bins (current usage accesses initial bin).

**Neuron energy table:**

- Rows: threshold voltage buckets (100 mV steps: 100–1000 mV).
- Columns: membrane voltage buckets (50 mV steps: 0–50 to 950–1000 mV).
- Values represent energy lookup per (Vth bucket, Vn bucket).
- Out-of-range buckets return 0.

## 2.8 Parser Behavior

- If `neuron_energy_table_path` or `synapses_energy_table_path` are present in the config file, their paths supersede XML-provided paths.
- Loading failures leave tables empty (resulting lookups return 0 without error escalation at parse stage).

## 2.9 Exposed Outputs

After integration:

- Aggregated synapse energy total (sum across all synapses).
- Aggregated neuron energy total (sum across all neuron lookups).

These totals are accessible through `NetworkParameters` consumers and printed by higher-level components (no change required in config structure to obtain them).

## 2.10 Validation & Fallback

- Missing keys: no energy CSV loaded (energy outputs default to zero).
- Malformed numeric cells: parser relies on `std::stod` (throws if unrecoverable).
- Empty data section after header: treated as load failure.

## 2.11 Practical Checklist

- Provide correctly formatted CSVs with at least one data row.
- Ensure paths in config are valid; relative paths are resolved from current working directory.
- Keep Vth and Vn coverage in neuron table consistent with defined bucket ranges (100–1000 mV, 0–1000 mV).
- Align synapse table row count with expected discrete weight classes.

## 2.12 Summary

New XML coverage adds DS configuration (bit width, clock, mode), BIU per-neuron scalar overrides (range and individual forms), and two new config file keys (CSV files) for calculating energy.

---

# 3. Using the NemoSim Simulation Tool

To use the NemoSim simulation tool, do the following:

1. Prepare the XML/TXT files, as described in Section 3.1
2. Prepare the JSON file, as described in Section 3.2
3. Run the NemoSim tool, as described in Section 3.3
4. Plot the output, as described in Section 3.4

## 3.1 Step 1: Preparing the XML/TXT Files

Do the following:

1. In an XML configuration file, define your network architecture, neuron parameters, and simulation settings.

   **Important:**
   - The XML file must have a `<NetworkConfig>` root with a `type` attribute.
   - Required child elements depend on the network type (LIF, BIU, and so on).
   - All required numeric fields must be present and valid numbers.

2. For example:

   **For a LIF network:**

   ```xml
   <NetworkConfig type="LIF">
     <LIFNetwork>
       <Cm>1.0</Cm>
       <Cf>0.5</Cf>
       <VDD>2.5</VDD>
       <!-- other LIF parameters -->
     </LIFNetwork>
     <Architecture>
       <Layer size="32"/>
       <YFlash rows="32" cols="32">
         <weights>
           <!-- weights here -->
         </weights>
       </YFlash>
       <!-- network connectivity, layers, weights, etc. -->
     </Architecture>
   </NetworkConfig>
   ```

   **Table 2-1** defines the key parameters that are used in this section of the LIF XML configuration file. These values are based on standard analog neuron circuit modeling practices and can be adapted depending on the simulation context.

   **Table 2-1: LIF Network XML Configuration Parameter Definitions**

   | Parameter | Description | Unit | Example Value | Notes |
   |-----------|-------------|------|---------------|-------|
   | Cm | Membrane capacitance | Farads (F) | 1e-6 | Determines the neuron integration time constant |
   | Cf | Feedback capacitance | Farads (F) | 1e-9 | Affects how quickly the membrane voltage resets or leaks after a spike |
   | VDD | Supply voltage | Volts (V) | 5.0 | Sets the upper voltage bounds for circuit behavior |
   | VTh | Threshold voltage | Volts (V) | 1.0 | Defines the spike generation threshold |
   | K | Gain factor | N/A | 2 | Dimensionless scaling factor (for example, for current mirror) |
   | Rmin/Rmax | Min/Max resistance in synaptic array | Ohms (Ω) | 145e3/145e6 | Used for dynamic range in weight representation |
   | gm | Transconductance | Siemens (S) | 6.896e-6 | Typically from the input differential pair |
   | CGB*, CGD*, CDB* | Parasitic capacitances (Gate-*, Drain-*, Bulk-*) | Farads (F) | ~e-18 values | Derived from transistor model extraction |
   | req | Effective resistance | Ohms (Ω) | 145e3 | Used in equivalent RC modeling |
   | R_da | Driver array resistance | Ohms (Ω) | 10e3 | Series resistance from driver circuitry |
   | dt | Simulation time step | Seconds (s) | 0.001 | Time increment for each simulation step |
   | IR | Input current scaling factor | Amperes (A) | 1e-10 | Multiplies the provided input values to obtain actual currents |

   **Note:** It's optional to define a YFlash between the layers. YFlash is a matrix of weights, in which:
   - Each weight holds a value that represents a resistance or diode that will be multiplied by the output of each neuron.
   - Each neuron connects to the corresponding row in the YFlash, and each column of the YFlash is connected to the corresponding entrance of each neuron in the next layer.

   **For a BIU network:**

   ```xml
   <NetworkConfig type="BIU">
     <BIUNetwork>
       <!-- BIU parameters here -->
     </BIUNetwork>
     <Architecture>
       <Layer size="1">
         <synapses rows="1" cols="1">
           <weights>
             <row>7.0</row>
           </weights>
         </synapses>
       </Layer>
       <!-- architecture details -->
     </Architecture>
   </NetworkConfig>
   ```

   Each layer has its own matrix of synapses that connects to the entrance of each neuron in the layer.

   **Table 2-2** defines the key parameters that are used in this section of the BIU XML configuration file. These values are based on a switched-capacitor SNN architecture using programmable digital weights, charge sharing, and comparator-based thresholding.

   **Table 2-2: BIU Network XML Configuration Parameter Definitions**

   | Parameter | Description | Unit | Example Value | Notes |
   |-----------|-------------|------|---------------|-------|
   | Cu | Synapse unit capacitance | Femtofarads (fF) | 4 | Defines the granularity of weight resolution |
   | Cn | Neuron integration capacitor | Femtofarads (fF) | 1000 | Large capacitor for temporal integration |
   | VDD | Supply voltage | Volts (V) | 1.2 | Nominal voltage for digital and analog circuitry |
   | VTh | Comparator threshold voltage | Volts (V) | ±0.4 | Spike generation threshold (programmable) |
   | WS | Weight sign | N/A | +1 or -1 | Positive = VDD, Negative = VSS |
   | W[3:0] | Synaptic weight (4-bit) | Digital | 0–15 | Multiplies the charge contribution per synapse |
   | Refractory | Refractory period (cycles) | Integer | 1–8 | Input is blocked for N cycles after spike |
   | Cl | Leakage capacitance (optional) | Femtofarads (fF) | 5e-15 | Models subthreshold leakage or passive decay |
   | Vm | Neuron potential | Volts (V) | Dynamic | Computed via charge-sharing at each phase |
   | Nu | Number of synaptic inputs | N/A | (varies by layer) | Determines the total Cu contribution per neuron |

3. In a plain TXT file, define the neuron values.

   **Important:**
   - Each line shall contain values corresponding to the neurons in the first layer (without delimiters), representing the input current for each time step (or input channel).

   **For example:**

   ```
   1 0 1 0 1 1 1 0
   0 0 1 0 1 1 1 0
   0 0 1 0 1 1 1 0
   0 0 1 0 1 1 1 0
   1 0 1 0 1 1 1 0
   ```

   **Tip:** You can use the provided Python `input_creator.py` script to generate input files; for example:

   ```python
   python input_creator.py
   > "1e-10 * math.sin(2 * math.pi * t * 5 + 3 * math.pi/2) + 1e-10"
   ```

## 3.2 Step 2: Preparing the JSON File

Do the following:

1. In a JSON file, define your workspace parameters and input files paths.

   **For example:**

   **For a LIF network:**

   ```json
   {
     "output_directory": "./Tests/SNN/LIF/sin_current_test/",
     "xml_config_path": "./Tests/SNN/LIF/sin_current_test/testFull.xml",
     "data_input_file": "./Tests/SNN/LIF/sin_current_test/input.txt",
     "progress_interval_seconds": 2
   }
   ```

   **For a BIU network:**

   ```json
   {
     "output_directory": "./Tests/SNN/BIU/",
     "xml_config_path": "./Tests/SNN/BIU/test.xml",
     "sup_xml_config_path": "./Tests/SNN/BIU/supervisor.xml",
     "data_input_file": "./Tests/SNN/BIU/input.txt",
     "progress_interval_seconds": 2
   }
   ```

   **Note:** `sup_xml_config_path` is an optional field used only by the BIU network; all other fields are used by both the LIF and BIU networks.

## 3.3 Step 3: Running the NemoSim Simulator Tool

Do the following:

1. From the root directory, type:

   ```bash
   NEMOSIM.exe <name of JSON file>
   ```

   **For example:**

   ```bash
   NEMOSIM.exe config.json
   ```

   **Alternative - Using the Python SDK:**

   If you're using the Python SDK (`nemosdk`), you can run simulations programmatically:

   ```python
   from nemosdk import NemoSimRunner
   from pathlib import Path
   
   runner = NemoSimRunner(working_dir=Path("bin/Linux"))
   result = runner.run(compiled_model, check=True)
   print(f"Return code: {result.returncode}")
   print(f"Logs: {result.stdout_path}, {result.stderr_path}")
   ```

   The SDK automatically captures stdout and stderr to log files and returns a `RunResult` object with the process exit code.

   **Binary Path Configuration:**

   The simulator binary path can be configured in three ways (in order of precedence):
   1. Explicit `binary_path` parameter: `NemoSimRunner(working_dir=Path("bin/Linux"), binary_path=Path("/custom/path"))`
   2. `NEMOSIM_BINARY` environment variable: `export NEMOSIM_BINARY=/custom/path/to/nemosim`
   3. Default: `working_dir / "NEMOSIM"` (e.g., `bin/Linux/NEMOSIM`)

2. While the NemoSim is running, it will display progress messages on the screen, as demonstrated in **Example 3-1**. If an error occurs, an error or warning message will be displayed (for details, see Section 4).

   **Example 3-1: NemoSim Progress Messages**

   *(Progress messages would be displayed here during simulation)*

## 3.4 Step 4: Plotting the Outputs

When the NemoSim has finished running, it generates output files and places them in the output directory you specified in the JSON file (as described in Section 3.2).

Output files are plain text, each containing a list of numeric values (one per line). Each output file corresponds to a specific neural variable, where `<x>` is the number of the layer, and `<y>` is the number of the neuron:

**LIF Simulation (three files per neuron):**

- `iins_<x>_<y>.txt`: Input currents
- `vms_<x>_<y>.txt`: Membrane potentials
- `vouts_<x>_<y>.txt`: Output voltages (spikes)

**BIU Simulation (three files per neuron):**

- `vin_<x>_<y>.txt`: Synapse input values
- `vns_<x>_<y>.txt`: Neural state potentials
- `spikes_<x>_<y>.txt`: Output spikes

**Note:** All output filenames use lowercase letters (e.g., `spikes_0_0.txt`, `vin_0_0.txt`, `vns_0_0.txt`).

After the output files have been generated, you can plot or analyze them to look for neurons with unexpected behaviors (for example, constant potentials or no spikes) for further debugging.

Do one of the following:

- For LIF networks, use the `plot_vm_to_dt.py` script.
- For BIU networks, use the `plot_vn_to_dt.py` script.

**For example:**

```bash
python plot_vm_to_dt.py iins_0_0.txt vms_0_0.txt vouts_0_0.txt
```

---

# 4. Error Handling

**Important:** All errors are considered to be critical, and will stop the NemoSim Simulator.

## 4.1 Error Message Formats

**Errors (examples):**

```
Error loading XML file: <description>
Error: No <NetworkConfig> root element found.
Error: Network type attribute not found in <NetworkConfig>.
```

## 4.2 Possible Return Codes

The NemoSim simulator uses standard process exit codes:

- **0**: Success - The simulation completed successfully
- **Non-zero**: Failure - The simulation encountered an error and stopped

When using the Python SDK (`nemosdk`), the `RunResult.returncode` field contains the process exit code. The SDK will raise a `RuntimeError` if `check=True` and the return code is non-zero.

**Internal Implementation Note:** The simulator internally uses TinyXML2 for XML parsing, which may produce internal error codes (such as `XML_SUCCESS`, `XML_ERROR_FILE_NOT_FOUND`, etc.). These are translated into process exit codes. Detailed error messages are written to the stderr log file, which can be accessed via `RunResult.stderr_path` when using the SDK.

---

# 5. References

- For details and example files for LIF, see `Tests/SNN/LIF/`.
- For details and example files for BIU, see `Tests/SNN/BIU/`.
- Output file examples: `vin.txt`, `vns.txt`, `spikes.txt` (in the test folders).
