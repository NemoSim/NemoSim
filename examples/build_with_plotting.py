#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def read_spike_data(spike_file: Path) -> np.ndarray:
    """Read spike data from a text file (one value per line: 0 or 1).
    
    Returns a 1D numpy array of spike events.
    """
    with spike_file.open() as f:
        data = [int(line.strip()) for line in f]
    return np.array(data, dtype=np.int32)


def plot_spike_raster(spike_files: list[Path], layer_idx: int, title: str, ax: plt.Axes) -> None:
    """Plot a spike raster for multiple neurons in a layer.
    
    Args:
        spike_files: List of spike file paths for this layer
        layer_idx: Layer index
        title: Plot title
        ax: Matplotlib axes to plot on
    """
    if not spike_files:
        return
    
    # Read all spike data
    spike_data = [read_spike_data(f) for f in spike_files]
    n_neurons = len(spike_data)
    
    # Create raster plot
    for neuron_idx, spikes in enumerate(spike_data):
        spike_times = np.where(spikes == 1)[0]
        if len(spike_times) > 0:
            ax.scatter(spike_times, [neuron_idx] * len(spike_times), 
                      s=10, c='k', marker='|', linewidths=0.5)
    
    ax.set_ylim(-0.5, n_neurons - 0.5)
    ax.set_xlabel('Time (ticks)', fontsize=10)
    ax.set_ylabel('Neuron Index', fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)


def plot_voltage_trace(vin_file: Path, title: str, ax: plt.Axes, max_samples: int = 10000) -> None:
    """Plot voltage trace from input voltage file.
    
    Args:
        vin_file: Path to voltage input file
        title: Plot title
        ax: Matplotlib axes to plot on
        max_samples: Maximum number of samples to plot (for performance)
    """
    with vin_file.open() as f:
        data = [float(line.strip()) for line in f]
    
    # Sample data if too large
    if len(data) > max_samples:
        indices = np.linspace(0, len(data) - 1, max_samples, dtype=int)
        data = [data[i] for i in indices]
        x = np.linspace(0, len(data), max_samples)
    else:
        x = np.arange(len(data))
    
    ax.plot(x, data, linewidth=0.5)
    ax.set_xlabel('Time (ticks)', fontsize=10)
    ax.set_ylabel('Voltage', fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)


def main() -> int:

    # Assumed parameters (no user input required)
    out_dir = Path("examples/out/with_plotting")
    sim_workdir = Path("bin/Linux")

    # Create a simple two-layer network
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
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
    )
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
    )

    # Compile and run
    print("Compiling network...")
    cfg_path = compile_model(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        data_input_file=(Path("tests/data/multi_layer_test/input.txt")).resolve(),
    )
    
    print("Running simulation...")
    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(cfg_path, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)

    # Plot results
    print("Generating plots...")
    output_dir = out_dir / "output"
    
    # Find all spike files
    spike_files_0 = sorted(output_dir.glob("spikes_0_*.txt"))
    spike_files_1 = sorted(output_dir.glob("spikes_1_*.txt"))
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('NemoSim Simulation Results', fontsize=16, fontweight='bold')
    
    # Plot spike rasters
    if spike_files_0:
        plot_spike_raster(spike_files_0, 0, 'Layer 0 Spike Raster', axes[0, 0])
    if spike_files_1:
        plot_spike_raster(spike_files_1, 1, 'Layer 1 Spike Raster', axes[0, 1])
    
    # Plot sample voltage traces
    vin_files = sorted(output_dir.glob("vin_0_*.txt"))
    vns_files = sorted(output_dir.glob("vns_1_*.txt"))
    
    if vin_files:
        plot_voltage_trace(vin_files[0], f'Layer 0 Input Voltage (Neuron 0)', axes[1, 0])
    if vns_files:
        plot_voltage_trace(vns_files[0], f'Layer 1 Voltage (Neuron 0)', axes[1, 1])
    
    plt.tight_layout()
    
    # Save plot
    plot_file = out_dir / "simulation_results.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {plot_file}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

