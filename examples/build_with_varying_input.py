#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def main() -> int:
    """Build and run a small network using varying in-memory input samples to test output changes."""
    out_dir = Path("examples/out/with_varying_input")
    sim_workdir = Path("bin/Linux")

    defaults = BIUNetworkDefaults(
        VTh=0.05,
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )

    # First layer has five neurons and consumes five distinct input channels.
    # Each neuron is wired to a unique column via an identity-matrix synapse.
    layer0 = Layer(
        size=5,
        synapses=Synapses(
            rows=5,
            cols=5,
            weights=[
                [6.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 5.5, 0.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 4.5, 0.0],
                [0.0, 0.0, 0.0, 0.0, 4.0],
            ],
        ),
        probe="inputs",
    )
    layer1 = Layer(
        size=1,
        synapses=Synapses(
            rows=1,
            cols=5,
            weights=[[3.0, 3.0, 3.0, 3.0, 3.0]],
        ),
        probe="output",
    )

    # Provide varied stimulus samples to test output changes.
    # Samples progress from low to high intensity to observe output variation.
    samples = [
        (0, 0, 0, 0, 0),      # No input - baseline
        (2, 2, 2, 2, 2),      # Low uniform input
        (5, 5, 5, 5, 5),      # Medium uniform input
        (10, 10, 10, 10, 10), # High uniform input
        (15, 0, 0, 0, 0),     # High input on first channel only
        (0, 15, 0, 0, 0),     # High input on second channel only
        (12, 12, 12, 12, 12), # Very high uniform input
        (8, 6, 10, 4, 12),    # Varied pattern
    ]

    compiled = compile_model(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        input_data=samples,
    )

    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(compiled, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)
    print()

    input_probe = compiled.get_probe("inputs")
    output_probe = compiled.get_probe("output")
    
    # Collect layer 0 neuron spikes
    layer0_spikes = {}
    print("Layer 0 (Input Layer) Neuron Spikes:")
    for neuron in input_probe.list_neuron_indices():
        try:
            spikes = input_probe.get_spikes(neuron)
            spike_count = sum(spikes)
            layer0_spikes[neuron] = spike_count
            print(f"  Neuron {neuron}: {spike_count} spikes")
        except FileNotFoundError:
            layer0_spikes[neuron] = 0
            print(f"  Neuron {neuron}: <no data>")
    print()

    # Check output neuron spikes
    try:
        out_spikes = output_probe.get_spikes(0)
        output_spike_count = sum(out_spikes)
        print(f"Layer 1 (Output Layer) Neuron Spikes: {output_spike_count}")
        print(f"Output spike times: {list(out_spikes) if out_spikes else 'none'}")
    except FileNotFoundError:
        output_spike_count = 0
        print("Output spikes: <no data>")
    print()

    # Analyze if outputs are changing
    print("=" * 60)
    print("Output Change Analysis:")
    print("=" * 60)
    
    # Check if layer 0 neurons have varying outputs
    layer0_values = list(layer0_spikes.values())
    if len(set(layer0_values)) > 1:
        print("✓ Layer 0 neurons show VARIED outputs across channels")
        print(f"  Spike counts range from {min(layer0_values)} to {max(layer0_values)}")
    else:
        print("✗ Layer 0 neurons show UNIFORM outputs (all same)")
        print(f"  All neurons have {layer0_values[0] if layer0_values else 0} spikes")
    
    # Check if output neuron is responding
    if output_spike_count > 0:
        print(f"✓ Output neuron is ACTIVE (fired {output_spike_count} times)")
    else:
        print("✗ Output neuron is INACTIVE (no spikes detected)")
    
    # Overall assessment
    total_input_activity = sum(layer0_spikes.values())
    if total_input_activity > 0 and output_spike_count > 0:
        print(f"\n✓ Network is RESPONSIVE:")
        print(f"  - Total input activity: {total_input_activity} spikes")
        print(f"  - Output activity: {output_spike_count} spikes")
        print(f"  - Output responds to varying inputs")
    elif total_input_activity > 0:
        print(f"\n⚠ Network receives input but output is silent:")
        print(f"  - Total input activity: {total_input_activity} spikes")
        print(f"  - Output activity: 0 spikes")
        print(f"  - May need higher input intensity or different weights")
    else:
        print("\n✗ Network shows NO ACTIVITY")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

