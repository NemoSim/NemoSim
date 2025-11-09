"""Tests for layer probe functionality.

These tests validate that the probe API correctly reads and returns data
that matches what's in the actual output files.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import threading
import time
import types

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model, CompiledModel
from nemosdk.probe_utils import watch_probe


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


def _compile_with_output(
    tmp_path: Path,
    layers: list[Layer],
    *,
    defaults: BIUNetworkDefaults,
    output_dir: Path,
) -> CompiledModel:
    """Compile layers with probes and rewrite config to point to `output_dir`."""
    model_dir = tmp_path / "model"
    model_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True, parents=True)

    input_file = tmp_path / "input.txt"
    input_file.write_text("0\n")

    compiled = compile_model(
        defaults=defaults,
        layers=layers,
        out_dir=model_dir,
        data_input_file=input_file,
    )

    config_path = compiled.get_config_path()
    with config_path.open() as f:
        cfg = json.load(f)
    cfg["output_directory"] = str(output_dir.resolve())
    with config_path.open("w") as f:
        json.dump(cfg, f, indent=2)

    return CompiledModel(config_path=config_path)


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
    
    # Create model with probe
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer0 = Layer(
        size=3,
        synapses=Synapses(rows=3, cols=2, weights=[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
        probe="test_layer",
    )

    compiled = _compile_with_output(
        tmp_path,
        [layer0],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0, layer1],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0],
        defaults=defaults,
        output_dir=output_dir,
    )

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
    
    compiled = _compile_with_output(
        tmp_path,
        [layer0, layer1, layer2],
        defaults=defaults,
        output_dir=tmp_path / "output_list",
    )

    probes = compiled.list_probes()
    assert "input" in probes
    assert "output" in probes
    assert len(probes) == 2, f"Expected 2 probes, got {len(probes)}: {probes}"


def test_probe_to_dataframe_with_stub_pandas(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    spikes = [0, 1, 0, 1]
    vin = [0.1, 0.2, 0.3, 0.4]
    (output_dir / "spikes_0_0.txt").write_text("\n".join(str(v) for v in spikes) + "\n")
    (output_dir / "vin_0_0.txt").write_text("\n".join(str(v) for v in vin) + "\n")

    defaults = BIUNetworkDefaults(VTh=0.5, RLeak=400e6, refractory=10, DSBitWidth=4, DSClockMHz=10)
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe0")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)
    probe = compiled.get_probe("probe0")

    fake_pd = types.ModuleType("pandas")
    fake_pd.DataFrame = lambda data: {"data": data}  # type: ignore[assignment]
    original_pandas = sys.modules.get("pandas")
    sys.modules["pandas"] = fake_pd
    try:
        df = probe.to_dataframe(neurons=[0], signals=("spikes", "vin"), sample_every=1)
        assert df == {"data": {"spikes_n0": spikes, "vin_n0": vin}}

        downsampled = probe.to_dataframe(neurons=[0], signals=("spikes",), sample_every=2, max_rows=2)
        assert downsampled == {"data": {"spikes_n0": [0, 0]}}
    finally:
        if original_pandas is not None:
            sys.modules["pandas"] = original_pandas
        else:
            sys.modules.pop("pandas", None)


def test_probe_iter_spikes_chunks(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    values = [0, 1, 0, 0, 1, 0, 1, 0, 0, 0]
    (output_dir / "spikes_0_0.txt").write_text("\n".join(str(v) for v in values) + "\n")

    defaults = BIUNetworkDefaults()
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)
    probe = compiled.get_probe("probe")

    chunks = list(probe.iter_spikes(0, chunk_size=4))
    assert chunks == [[0, 1, 0, 0], [1, 0, 1, 0], [0, 0]]


def test_probe_iter_all_spikes(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    data = {
        (0, 0): [0, 1, 0, 1, 0],
        (0, 1): [1, 0, 1, 0, 1],
    }
    for (layer_idx, neuron_idx), seq in data.items():
        (output_dir / f"spikes_{layer_idx}_{neuron_idx}.txt").write_text("\n".join(str(v) for v in seq) + "\n")

    defaults = BIUNetworkDefaults()
    layer = Layer(size=2, synapses=Synapses(rows=2, cols=1, weights=[[1.0], [1.0]]), probe="probe")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)
    probe = compiled.get_probe("probe")

    results = list(probe.iter_all_spikes(chunk_size=3))
    expected = [
        (0, [0, 1, 0]),
        (0, [1, 0]),
        (1, [1, 0, 1]),
        (1, [0, 1]),
    ]
    assert results == expected


def test_probe_list_neuron_indices(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    for neuron_idx in range(3):
        (output_dir / f"spikes_0_{neuron_idx}.txt").write_text("0\n")

    defaults = BIUNetworkDefaults()
    layer = Layer(size=3, synapses=Synapses(rows=3, cols=1, weights=[[1.0], [1.0], [1.0]]), probe="probe")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)
    probe = compiled.get_probe("probe")
    assert probe.list_neuron_indices() == [0, 1, 2]


def test_probes_json_written(tmp_path: Path):
    defaults = BIUNetworkDefaults()
    layer = Layer(size=2, synapses=Synapses(rows=2, cols=1, weights=[[1.0], [1.0]]), probe="probe")
    input_file = tmp_path / "input.txt"
    input_file.write_text("0\n")
    compiled = compile_model(
        defaults=defaults,
        layers=[layer],
        out_dir=tmp_path / "model",
        data_input_file=input_file,
    )
    probes_path = compiled.get_config_path().parent / "probes.json"
    assert probes_path.exists(), "Expected probes.json to be written"
    data = json.loads(probes_path.read_text())
    assert data["probes"][0]["name"] == "probe"
    assert data["probes"][0]["layer_index"] == 0
    assert data["probes"][0]["layer_size"] == 2


def test_compiled_model_reads_probe_metadata_from_disk(tmp_path: Path):
    output_dir = tmp_path / "output"
    defaults = BIUNetworkDefaults()
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)

    fresh = CompiledModel(config_path=compiled.get_config_path())
    assert fresh.list_probes() == ["probe"]
    meta = fresh.get_probe_metadata("probe")
    assert meta.layer_index == 0
    assert meta.layer_size == 1


def test_watch_probe_follow(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    file_path = output_dir / "spikes_0_0.txt"
    file_path.write_text("0\n")

    defaults = BIUNetworkDefaults()
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    compiled = _compile_with_output(tmp_path, [layer], defaults=defaults, output_dir=output_dir)
    probe = compiled.get_probe("probe")

    def writer():
        time.sleep(0.05)
        with file_path.open("a") as fh:
            fh.write("1\n2\n")

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        values = list(
            watch_probe(
                probe,
                "spikes",
                0,
                follow=True,
                poll_interval=0.01,
                max_events=3,
            )
        )
    finally:
        thread.join()

    assert values == [0, 1, 2]

