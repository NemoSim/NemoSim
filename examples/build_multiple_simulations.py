#!/usr/bin/env python3
"""Run 10 different simulations with constant inputs (1-10) for 1 second each.

This example demonstrates:
1. Running multiple separate simulations
2. Each simulation has a constant input value (1, 2, 3, ..., 10)
3. Each simulation runs for 1 second
4. Collecting firing frequency for each simulation
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


def run_single_simulation(
    input_value: float,
    simulation_duration_steps: int,
    out_dir: Path,
    sim_workdir: Path,
    defaults: BIUNetworkDefaults,
    layer: Layer,
) -> tuple[int, float]:
    """Run a single simulation with constant input value.
    
    Returns:
        tuple: (total_spikes, firing_rate)
    """
    # Create constant input for the entire simulation duration
    samples = [(input_value,) for _ in range(simulation_duration_steps)]
    
    # Create unique output directory for this simulation
    # Replace decimal point with underscore for directory name (e.g., 0.5 -> input_0_5)
    dir_name = f"input_{str(input_value).replace('.', '_')}"
    sim_out_dir = out_dir / dir_name
    sim_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Compile the model
    compiled = compile_model(
        defaults=defaults,
        layers=[layer],
        include_supervisor=True,
        out_dir=sim_out_dir,
        input_data=samples,
    )
    
    # Run the simulation
    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(compiled, check=True)
    
    # Get spikes
    output_probe = compiled.get_probe("output")
    try:
        spikes = output_probe.get_spikes(0)
        spike_count = sum(spikes)
        num_time_steps = len(spikes)
        firing_rate = spike_count / num_time_steps if num_time_steps > 0 else 0.0
        return spike_count, firing_rate
    except FileNotFoundError:
        return 0, 0.0


def main() -> int:
    """Run 10 simulations with inputs 1-10, each for 1 second."""
    base_out_dir = Path("examples/out/multiple_simulations")
    sim_workdir = Path("bin/Linux")
    
    # Simulation parameters
    num_simulations = 10
    # Start at 0.5 and increment by 0.5: [0.5, 1.0, 1.5, 2.0, ..., 5.0]
    input_values = [0.5 + i * 0.5 for i in range(num_simulations)]
    
    # For 1 second simulation: assuming 1ms per time step = 1000 steps per second
    # Adjust this based on your actual time step duration
    simulation_duration_steps = 1000  # 1 second at 1ms per step
    time_step_duration_seconds = 0.001  # 1ms per time step
    simulation_duration_seconds = simulation_duration_steps * time_step_duration_seconds  # 1 second
    
    defaults = BIUNetworkDefaults(
        VTh=0.01,  # Lower threshold to make it easier to fire
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )
    
    # Single neuron layer with weight=1
    layer = Layer(
        size=1,
        synapses=Synapses(
            rows=1,
            cols=1,
            weights=[[1.0]],
        ),
        probe="output",
    )
    
    print("=" * 70)
    print(f"Running {num_simulations} Simulations (Input Values {input_values[0]:.1f}-{input_values[-1]:.1f}, 1 second each)")
    print("=" * 70)
    print(f"Simulation duration: {simulation_duration_steps} time steps ({simulation_duration_seconds:.3f} seconds)")
    print(f"Time step duration: {time_step_duration_seconds*1000:.1f} ms")
    print(f"Input values: {input_values}")
    print()
    
    # Run all simulations
    results = []
    for i, input_val in enumerate(input_values, 1):
        print(f"[{i}/{num_simulations}] Running simulation with input={input_val:.1f}...", end=" ", flush=True)
        spike_count, firing_rate = run_single_simulation(
            input_value=input_val,
            simulation_duration_steps=simulation_duration_steps,
            out_dir=base_out_dir,
            sim_workdir=sim_workdir,
            defaults=defaults,
            layer=layer,
        )
        # Calculate firing rate in Hz (spikes per second)
        firing_rate_hz = spike_count / simulation_duration_seconds
        
        results.append({
            'input': input_val,
            'spikes': spike_count,
            'firing_rate_per_step': firing_rate,
            'firing_rate_hz': firing_rate_hz,
        })
        print(f"Done! Spikes: {spike_count}, Rate: {firing_rate_hz:.2f} Hz")
    
    print()
    print("=" * 70)
    print("Simulation Results Summary")
    print("=" * 70)
    print(f"{'Input Value':<15} {'Total Spikes':<15} {'Firing Rate (Hz)':<20}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['input']:<15.1f} {result['spikes']:<15} {result['firing_rate_hz']:<20.2f}")
    
    # Create plot
    if HAS_PLOTTING:
        print("\n" + "=" * 70)
        print("Generating plot...")
        print("=" * 70)
        
        input_vals = [r['input'] for r in results]
        firing_rates_hz = [r['firing_rate_hz'] for r in results]
        spike_counts = [r['spikes'] for r in results]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot 1: Input vs Firing Rate in Hz
        ax1.plot(input_vals, firing_rates_hz, 'o-', linewidth=2, markersize=10, 
                color='steelblue', markerfacecolor='lightblue', markeredgewidth=2)
        ax1.set_xlabel('Input Value', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Firing Rate (Hz)', fontsize=12, fontweight='bold')
        ax1.set_title('Input vs Firing Frequency\n(10 Simulations, 1 second each)', 
                      fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlim(0, max(input_vals) + 1)
        ax1.set_ylim(-1, max(firing_rates_hz) * 1.1 if firing_rates_hz else 100)
        
        # Add value labels on points
        for x, y in zip(input_vals, firing_rates_hz):
            ax1.annotate(f'{y:.1f} Hz', (x, y), textcoords="offset points", 
                        xytext=(0, 10), ha='center', fontsize=9)
        
        # Plot 2: Input vs Total Spikes
        ax2.bar(input_vals, spike_counts, color='steelblue', alpha=0.7, edgecolor='navy', linewidth=1.5)
        ax2.set_xlabel('Input Value', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Total Spikes', fontsize=12, fontweight='bold')
        ax2.set_title('Input vs Total Spikes\n(10 Simulations, 1 second each)', 
                     fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax2.set_xlim(0, max(input_vals) + 1)
        
        # Add value labels on bars
        for x, y in zip(input_vals, spike_counts):
            if y > 0:
                ax2.annotate(f'{y}', (x, y), textcoords="offset points", 
                            xytext=(0, 5), ha='center', fontsize=9)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = base_out_dir / "simulation_results.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {plot_file}")
        plt.close()
    else:
        print("\n" + "=" * 70)
        print("Plotting skipped (matplotlib not available)")
        print("=" * 70)
        print("To enable plotting, install matplotlib and numpy:")
        print("  python3 -m pip install --user matplotlib numpy")
        print("  # or using system package manager:")
        print("  # sudo apt install python3-matplotlib python3-numpy")
    
    # Save results to CSV
    csv_file = base_out_dir / "results.csv"
    with csv_file.open('w') as f:
        f.write("input_value,total_spikes,firing_rate_per_step,firing_rate_hz\n")
        for result in results:
            f.write(f"{result['input']},{result['spikes']},{result['firing_rate_per_step']:.6f},{result['firing_rate_hz']:.2f}\n")
    print(f"\nResults saved to CSV: {csv_file}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

