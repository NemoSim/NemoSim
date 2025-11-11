#!/usr/bin/env python3
"""Example demonstrating layer probes for easy data access.

This example shows how to:
1. Define probes on layers
2. Access layer data by probe name after simulation
3. Use the probe API to read spikes, vin, and vns data
"""
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile
from nemosdk.runner import NemoSimRunner


def main() -> int:

    # Create a simple two-layer network with probes
    defaults = BIUNetworkDefaults(
        VTh=0.6,
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )
    
    # Layer 0: input layer with probe "input"
    layer0 = Layer(
        size=3,
        synapses=Synapses(
            rows=3,
            cols=8,
            weights=[
                [6, 5, 5, 5, 5, -5, 5, 5],
                [5, -5, 5, 5, -5, 5, 5, 5],
                [4, 5, 5, -5, 5, 5, 5, 5],
            ],
        ),
        probe="input",  # Assign probe name
    )
    
    # Layer 1: output layer with probe "output"
    layer1 = Layer(
        size=7,
        synapses=Synapses(
            rows=7,
            cols=3,
            weights=[
                [7.0, 0.0, 0.0],
                [0.0, 7.0, 0.0],
                [0.0, 0.0, 7.0],
                [7, 7, 0.0],
                [0, 0, 1],
                [3, 0.0, 3],
                [5, 10, 5],
            ],
        ),
        probe="output",  # Assign probe name
    )

    # Compile the model
    out_dir = Path("examples/out/with_probes")
    sim_workdir = Path("bin/Linux")
    
    print("Compiling network...")
    compiled_model = compile(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        data_input_file=(Path("tests/data/multi_layer_test/input.txt")).resolve(),
    )
    
    # List available probes
    print(f"Available probes: {compiled_model.list_probes()}")
    
    # Run simulation
    print("Running simulation...")
    runner = NemoSimRunner(working_dir=sim_workdir)
    result = runner.run(compiled_model, check=True)
    print(f"Simulation completed with return code: {result.returncode}")
    
    # Access data using probes
    print("\nAccessing layer data via probes...")
    
    # Get probe for input layer
    input_probe = compiled_model.get_probe("input")
    print(f"\nInput layer (layer {input_probe.layer_idx}):")
    
    # Get spikes for neuron 0
    spikes_0 = input_probe.get_spikes(0)
    print(f"  Neuron 0 spikes: {sum(spikes_0)} total spikes in {len(spikes_0)} time steps")
    
    # Get all spikes for the layer
    all_spikes = input_probe.get_all_spikes()
    print(f"  Total neurons with data: {len(all_spikes)}")
    
    # Get probe for output layer
    output_probe = compiled_model.get_probe("output")
    print(f"\nOutput layer (layer {output_probe.layer_idx}):")
    
    # Get spikes for neuron 0
    output_spikes_0 = output_probe.get_spikes(0)
    print(f"  Neuron 0 spikes: {sum(output_spikes_0)} total spikes in {len(output_spikes_0)} time steps")
    
    # Get vin (input voltage) for neuron 0
    vin_0 = output_probe.get_vin(0)
    print(f"  Neuron 0 vin: {len(vin_0)} time steps, first value: {vin_0[0]:.4f}")
    
    # Get vns (neural state) for neuron 0
    vns_0 = output_probe.get_vns(0)
    print(f"  Neuron 0 vns: {len(vns_0)} time steps, first value: {vns_0[0]:.4f}")
    
    # Get all data for all neurons
    all_vin = output_probe.get_all_vin()
    all_vns = output_probe.get_all_vns()
    print(f"  Total neurons with data: {len(all_vin)} vin, {len(all_vns)} vns")
    
    print("\nExample completed successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

