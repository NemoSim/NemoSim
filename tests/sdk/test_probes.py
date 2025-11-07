"""Tests for layer probe functionality.

These tests validate that the probe API correctly reads and returns data
that matches what's in the actual output files.
"""
from __future__ import annotations

from pathlib import Path
import json

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model


def _read_file_directly(output_dir: Path, file_type: str, layer_idx: int, neuron_idx: int) -> list[float | int]:
    """Read a data file directly from the output directory.
    
    Args:
        output_dir: Output directory path
        file_type: One of 'spikes', 'vin', 'vns'
        layer_idx: Layer index
        neuron_idx: Neuron index
        
    Returns:
        List of values from the file
    """
    filename = f"{file_type}_{layer_idx}_{neuron_idx}.txt"
    filepath = output_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with filepath.open() as f:
        lines = [line.strip() for line in f if line.strip()]
        if file_type == "spikes":
            return [int(line) for line in lines]
        else:
            return [float(line) for line in lines]


def test_probe_spikes_matches_file(tmp_path: Path):
    """Test that probe.get_spikes() returns data matching the file."""
    # Create test output files first
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create spike files for layer 0, neurons 0-2
    test_spikes = {
        (0, 0): [0, 1, 0, 0, 1, 0, 1, 0, 0, 0],
        (0, 1): [1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
        (0, 2): [0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
    }
    
    for (layer, neuron), spikes in test_spikes.items():
        spike_file = output_dir / f"spikes_{layer}_{neuron}.txt"
        spike_file.write_text("\n".join(str(s) for s in spikes) + "\n")
    
    # Write input file (required for compile)
    (tmp_path / "input.txt").write_text("0\n")
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=3,
        synapses=Synapses(rows=3, cols=2, weights=[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
        probe="test_layer",
    )
    
    # Compile model (this creates the probe mapping)
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config to point to our test output directory
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    probe = compiled.get_probe("test_layer")
    
    # Compare probe output with direct file reads
    for neuron_idx in [0, 1, 2]:
        probe_data = probe.get_spikes(neuron_idx)
        file_data = _read_file_directly(output_dir, "spikes", 0, neuron_idx)
        
        assert probe_data == file_data, (
            f"Mismatch for neuron {neuron_idx}: "
            f"probe={probe_data}, file={file_data}"
        )
        assert probe_data == test_spikes[(0, neuron_idx)], (
            f"Probe data doesn't match expected: {probe_data} != {test_spikes[(0, neuron_idx)]}"
        )


def test_probe_vin_matches_file(tmp_path: Path):
    """Test that probe.get_vin() returns data matching the file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create vin files for layer 1, neurons 0-2
    test_vin = {
        (1, 0): [0.1, 0.2, 0.3, 0.4, 0.5],
        (1, 1): [0.6, 0.7, 0.8, 0.9, 1.0],
        (1, 2): [1.1, 1.2, 1.3, 1.4, 1.5],
    }
    
    for (layer, neuron), values in test_vin.items():
        vin_file = output_dir / f"vin_{layer}_{neuron}.txt"
        vin_file.write_text("\n".join(str(v) for v in values) + "\n")
    
    # Write input file
    (tmp_path / "input.txt").write_text("0\n")
    
    # Create model with probe for layer 1
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=2,
        synapses=Synapses(rows=2, cols=1, weights=[[1.0], [2.0]]),
    )
    layer1 = Layer(
        size=3,
        synapses=Synapses(rows=3, cols=2, weights=[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
        probe="output_layer",
    )
    
    # Compile model
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0, layer1],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config to point to test output
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    probe = compiled.get_probe("output_layer")
    
    # Compare probe output with direct file reads
    for neuron_idx in [0, 1, 2]:
        probe_data = probe.get_vin(neuron_idx)
        file_data = _read_file_directly(output_dir, "vin", 1, neuron_idx)
        
        assert len(probe_data) == len(file_data), (
            f"Length mismatch for neuron {neuron_idx}: "
            f"probe={len(probe_data)}, file={len(file_data)}"
        )
        assert probe_data == file_data, (
            f"Mismatch for neuron {neuron_idx}: "
            f"probe={probe_data}, file={file_data}"
        )
        assert probe_data == test_vin[(1, neuron_idx)], (
            f"Probe data doesn't match expected: {probe_data} != {test_vin[(1, neuron_idx)]}"
        )


def test_probe_vns_matches_file(tmp_path: Path):
    """Test that probe.get_vns() returns data matching the file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create vns files
    test_vns = {
        (0, 0): [0.5, 0.6, 0.7, 0.8, 0.9],
        (0, 1): [1.0, 1.1, 1.2, 1.3, 1.4],
    }
    
    for (layer, neuron), values in test_vns.items():
        vns_file = output_dir / f"vns_{layer}_{neuron}.txt"
        vns_file.write_text("\n".join(str(v) for v in values) + "\n")
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=2,
        synapses=Synapses(rows=2, cols=1, weights=[[1.0], [2.0]]),
        probe="input_layer",
    )
    
    # Compile model
    (tmp_path / "input.txt").write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    probe = compiled.get_probe("input_layer")
    
    # Compare probe output with direct file reads
    for neuron_idx in [0, 1]:
        probe_data = probe.get_vns(neuron_idx)
        file_data = _read_file_directly(output_dir, "vns", 0, neuron_idx)
        
        assert probe_data == file_data, (
            f"Mismatch for neuron {neuron_idx}: "
            f"probe={probe_data}, file={file_data}"
        )
        assert probe_data == test_vns[(0, neuron_idx)], (
            f"Probe data doesn't match expected: {probe_data} != {test_vns[(0, neuron_idx)]}"
        )


def test_probe_get_all_matches_files(tmp_path: Path):
    """Test that get_all_* methods return data matching all files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create multiple files for layer 0
    test_data = {
        "spikes": {(0, 0): [1, 0, 1], (0, 1): [0, 1, 0], (0, 2): [1, 1, 0]},
        "vin": {(0, 0): [0.1, 0.2, 0.3], (0, 1): [0.4, 0.5, 0.6], (0, 2): [0.7, 0.8, 0.9]},
        "vns": {(0, 0): [1.0, 1.1, 1.2], (0, 1): [1.3, 1.4, 1.5], (0, 2): [1.6, 1.7, 1.8]},
    }
    
    for file_type, data_dict in test_data.items():
        for (layer, neuron), values in data_dict.items():
            filepath = output_dir / f"{file_type}_{layer}_{neuron}.txt"
            filepath.write_text("\n".join(str(v) for v in values) + "\n")
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=3,
        synapses=Synapses(rows=3, cols=1, weights=[[1.0], [2.0], [3.0]]),
        probe="test_layer",
    )
    
    # Compile model
    (tmp_path / "input.txt").write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    probe = compiled.get_probe("test_layer")
    
    # Test get_all_spikes
    all_spikes = probe.get_all_spikes()
    assert len(all_spikes) == 3, f"Expected 3 neurons, got {len(all_spikes)}"
    for neuron_idx in [0, 1, 2]:
        assert neuron_idx in all_spikes, f"Neuron {neuron_idx} missing from all_spikes"
        assert all_spikes[neuron_idx] == test_data["spikes"][(0, neuron_idx)]
    
    # Test get_all_vin
    all_vin = probe.get_all_vin()
    assert len(all_vin) == 3, f"Expected 3 neurons, got {len(all_vin)}"
    for neuron_idx in [0, 1, 2]:
        assert neuron_idx in all_vin, f"Neuron {neuron_idx} missing from all_vin"
        assert all_vin[neuron_idx] == test_data["vin"][(0, neuron_idx)]
    
    # Test get_all_vns
    all_vns = probe.get_all_vns()
    assert len(all_vns) == 3, f"Expected 3 neurons, got {len(all_vns)}"
    for neuron_idx in [0, 1, 2]:
        assert neuron_idx in all_vns, f"Neuron {neuron_idx} missing from all_vns"
        assert all_vns[neuron_idx] == test_data["vns"][(0, neuron_idx)]


def test_probe_missing_file_raises_error(tmp_path: Path):
    """Test that probe methods raise FileNotFoundError for missing files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=1,
        synapses=Synapses(rows=1, cols=1, weights=[[1.0]]),
        probe="test_layer",
    )
    
    # Compile model
    (tmp_path / "input.txt").write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    probe = compiled.get_probe("test_layer")
    
    # Test that missing files raise FileNotFoundError
    try:
        probe.get_spikes(0)
        assert False, "Expected FileNotFoundError for missing spikes file"
    except FileNotFoundError:
        pass
    
    try:
        probe.get_vin(0)
        assert False, "Expected FileNotFoundError for missing vin file"
    except FileNotFoundError:
        pass
    
    try:
        probe.get_vns(0)
        assert False, "Expected FileNotFoundError for missing vns file"
    except FileNotFoundError:
        pass


def test_probe_invalid_name_raises_keyerror(tmp_path: Path):
    """Test that get_probe() raises KeyError for invalid probe names."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=1,
        synapses=Synapses(rows=1, cols=1, weights=[[1.0]]),
        probe="valid_probe",
    )
    
    # Compile model
    (tmp_path / "input.txt").write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Update config
    config_path = compiled.get_config_path()
    with config_path.open() as f:
        config = json.load(f)
    config["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(config, f, indent=2)
    
    # Use the compiled model (it already has the probe mapping)
    # Test that invalid probe name raises KeyError
    try:
        compiled.get_probe("invalid_probe")
        assert False, "Expected KeyError for invalid probe name"
    except KeyError as e:
        assert "invalid_probe" in str(e)
        assert "valid_probe" in str(e)  # Should list available probes


def test_probe_list_probes(tmp_path: Path):
    """Test that list_probes() returns all available probe names."""
    # Create model with multiple probes
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=1,
        synapses=Synapses(rows=1, cols=1, weights=[[1.0]]),
        probe="input",
    )
    layer1 = Layer(
        size=1,
        synapses=Synapses(rows=1, cols=1, weights=[[1.0]]),
        probe="output",
    )
    layer2 = Layer(
        size=1,
        synapses=Synapses(rows=1, cols=1, weights=[[1.0]]),
        # No probe for this layer
    )
    
    # Compile model
    (tmp_path / "input.txt").write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer0, layer1, layer2],
        out_dir=tmp_path / "model",
        data_input_file=tmp_path / "input.txt",
    )
    
    # Check that list_probes returns only layers with probes
    probes = compiled.list_probes()
    assert "input" in probes
    assert "output" in probes
    assert len(probes) == 2, f"Expected 2 probes, got {len(probes)}: {probes}"

