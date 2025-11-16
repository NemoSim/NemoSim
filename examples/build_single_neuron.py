#!/usr/bin/env python3
"""Example with a single neuron with weight=1.

This example demonstrates:
1. Creating a single neuron network
2. Providing several input values
3. Sampling the firing rate at the end
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path so nemosdk can be imported
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def main() -> int:
    """Build and run a single neuron network with weight=1 and sample firing rate."""
    out_dir = Path("examples/out/single_neuron")
    sim_workdir = Path("bin/Linux")

    defaults = BIUNetworkDefaults(
        VTh=0.01,  # Lower threshold to make it easier to fire
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )

    # Single neuron layer with weight=1
    # The synapse connects 1 input channel to 1 neuron with weight 1.0
    layer = Layer(
        size=1,
        synapses=Synapses(
            rows=1,
            cols=1,
            weights=[[1.0]],
        ),
        probe="output",
    )

    # Provide several input values to test different firing rates
    # Each input value is repeated multiple times to allow charge accumulation
    # Note: With weight=1.0, we need sufficient input values to reach threshold
    samples_per_value = 20  # Repeat each value this many times
    input_values = [
        0,      # No input - baseline
        5,      # Low input
        10,     # Medium input
        15,     # High input
        20,     # Very high input
        25,     # Extremely high input
        12,     # Medium-high input
        8,      # Low-medium input
    ]
    
    # Repeat each input value multiple times
    samples = [(val,) for val in input_values for _ in range(samples_per_value)]

    compiled = compile_model(
        defaults=defaults,
        layers=[layer],
        include_supervisor=True,
        out_dir=out_dir,
        input_data=samples,
    )

    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(compiled, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)
    print()

    # Get probe for the output neuron
    output_probe = compiled.get_probe("output")
    
    # Get spikes for the single neuron
    try:
        spikes = output_probe.get_spikes(0)
        spike_count = sum(spikes)
        num_time_steps = len(spikes)
        
        print("=" * 60)
        print("Single Neuron Results:")
        print("=" * 60)
        print(f"Total spikes: {spike_count}")
        print(f"Total time steps: {num_time_steps}")
        
        # Calculate firing rate (spikes per time step)
        if num_time_steps > 0:
            firing_rate = spike_count / num_time_steps
            print(f"Firing rate: {firing_rate:.4f} spikes/time step")
            print(f"Firing rate: {firing_rate * 100:.2f}%")
        
        # Show spike times
        spike_times = [i for i, spike in enumerate(spikes) if spike > 0]
        if spike_times:
            print(f"Spike times: {spike_times[:20]}{'...' if len(spike_times) > 20 else ''}")
            print(f"Total spike events: {len(spike_times)}")
        else:
            print("No spikes detected")
        
        # Show input values and corresponding activity
        print("\n" + "=" * 60)
        print("Input vs Output Analysis:")
        print("=" * 60)
        print(f"{'Input Value':<15} {'Spikes':<10} {'Firing Rate':<15}")
        print("-" * 60)
        
        # Group spikes by input value (each value was repeated samples_per_value times)
        # Store data for plotting
        input_data = []
        firing_rates = []
        
        if num_time_steps > 0:
            steps_per_value = samples_per_value
            for i, input_val in enumerate(input_values):
                start_idx = i * steps_per_value
                end_idx = (i + 1) * steps_per_value if i < len(input_values) - 1 else num_time_steps
                value_spikes = sum(spikes[start_idx:end_idx])
                value_steps = end_idx - start_idx
                value_rate = value_spikes / value_steps if value_steps > 0 else 0.0
                print(f"{input_val:<15} {value_spikes:<10} {value_rate:.4f}")
                
                # Store for plotting
                input_data.append(input_val)
                firing_rates.append(value_rate)
        
        # Create plot of input vs firing frequency
        if HAS_PLOTTING:
            print("\n" + "=" * 60)
            print("Generating plot...")
            print("=" * 60)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(input_data, firing_rates, 'o-', linewidth=2, markersize=8, color='steelblue', markerfacecolor='lightblue', markeredgewidth=2)
            ax.set_xlabel('Input Value', fontsize=12, fontweight='bold')
            ax.set_ylabel('Firing Rate (spikes/time step)', fontsize=12, fontweight='bold')
            ax.set_title('Input vs Firing Frequency\n(Single Neuron, Weight=1.0)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(-1, max(input_data) + 1)
            ax.set_ylim(-0.01, max(firing_rates) * 1.1 if firing_rates else 0.1)
            
            # Add value labels on points
            for x, y in zip(input_data, firing_rates):
                ax.annotate(f'{y:.3f}', (x, y), textcoords="offset points", 
                           xytext=(0, 10), ha='center', fontsize=9)
            
            plt.tight_layout()
            
            # Save plot
            plot_file = out_dir / "input_vs_firing_rate.png"
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {plot_file}")
            plt.close()
        else:
            print("\n" + "=" * 60)
            print("Plotting skipped (matplotlib not available)")
            print("=" * 60)
            print("To enable plotting, install matplotlib and numpy:")
            print("  python3 -m pip install --user matplotlib numpy")
            print("  # or using system package manager:")
            print("  # sudo apt install python3-matplotlib python3-numpy")
            print("\nNote: Plotting is optional. All data is still available in the output above.")
        
    except FileNotFoundError:
        print("Output spikes: <no data>")
        return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

