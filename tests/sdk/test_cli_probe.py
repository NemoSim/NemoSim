from __future__ import annotations

import contextlib
from io import StringIO
from pathlib import Path
import json
import sys
import threading
import time

from nemosdk import cli
from nemosdk.compiler import compile as compile_model
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses


def _compile_with_output(tmp_path: Path, layers: list[Layer], output_dir: Path) -> Path:
    """Compile layers and return the config.json path."""
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = tmp_path / "input.txt"
    input_file.write_text("0\n")

    defaults = BIUNetworkDefaults()
    compiled = compile_model(
        defaults=defaults,
        layers=layers,
        out_dir=model_dir,
        data_input_file=input_file,
    )

    config_path = compiled.get_config_path()
    cfg = json.loads(config_path.read_text())
    cfg["output_directory"] = str(output_dir.resolve())
    config_path.write_text(json.dumps(cfg, indent=2))
    return config_path


def _run_cli(args: list[str]) -> str:
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main(args)
    return buf.getvalue()


def test_cli_probe_list(tmp_path: Path):
    output_dir = tmp_path / "output"
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    config_path = _compile_with_output(tmp_path, [layer], output_dir)
    output = _run_cli(["probe", str(config_path), "--list"])
    assert "probe" in output


def test_cli_probe_show_head(tmp_path: Path):
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "spikes_0_0.txt").write_text("\n".join(str(v) for v in [0, 1, 0, 1]) + "\n")
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    config_path = _compile_with_output(tmp_path, [layer], output_dir)
    output = _run_cli(["probe", str(config_path), "--probe", "probe", "--signal", "spikes", "--head", "2"])
    assert "[spikes] neuron 0" in output
    assert "0, 1" in output.replace("\n", " ")


def test_cli_probe_follow(tmp_path: Path):
    output_dir = tmp_path / "output"
    file_path = output_dir / "spikes_0_0.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("0\n")
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]), probe="probe")
    config_path = _compile_with_output(tmp_path, [layer], output_dir)

    def writer():
        time.sleep(0.05)
        with file_path.open("a") as fh:
            fh.write("1\n")

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        output = _run_cli([
            "probe",
            str(config_path),
            "--probe",
            "probe",
            "--signal",
            "spikes",
            "--follow",
            "--max-events",
            "2",
            "--poll-interval",
            "0.01",
        ])
    finally:
        thread.join()

    assert "[spikes] neuron 0: 0" in output
    assert "[spikes] neuron 0: 1" in output
