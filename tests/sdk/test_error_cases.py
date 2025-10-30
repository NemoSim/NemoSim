from __future__ import annotations

from pathlib import Path
import os
import pytest

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses, NeuronOverrideRange
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner
from nemosdk.compiler import CompiledModel


def test_invalid_ds_mode_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=10, DSMode="NotAMode")
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]))
    with pytest.raises(ValueError):
        compile_model(defaults, [layer])


def test_missing_weights_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=10)
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[]))
    with pytest.raises(ValueError):
        compile_model(defaults, [layer])


def test_cols_mismatch_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=10)
    syn = Synapses(rows=1, cols=2, weights=[[1.0]])  # only 1 col provided
    layer = Layer(size=1, synapses=syn)
    with pytest.raises(ValueError):
        layer.validate()


def test_negative_layer_size_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=10)
    syn = Synapses(rows=1, cols=1, weights=[[1.0]])
    layer = Layer(size=0, synapses=syn)
    with pytest.raises(ValueError):
        layer.validate()


def test_range_start_gt_end_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=10)
    syn = Synapses(rows=1, cols=1, weights=[[1.0]])
    layer = Layer(size=1, synapses=syn, ranges=[NeuronOverrideRange(start=2, end=1, VTh=0.2)])
    with pytest.raises(ValueError):
        layer.validate()


def _make_failing_binary(dir_path: Path) -> Path:
    bin_path = dir_path / "NEMOSIM"
    bin_path.write_text("#!/usr/bin/env bash\nexit 2\n", encoding="utf-8")
    os.chmod(bin_path, 0o755)
    return bin_path


def test_runner_nonzero_exit_check_false_returns(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_failing_binary(work)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    res = runner.run(CompiledModel(config_path=cfg), check=False)
    assert res.returncode != 0


def test_runner_nonzero_exit_check_true_raises(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_failing_binary(work)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    with pytest.raises(RuntimeError):
        runner.run(CompiledModel(config_path=cfg), check=True)



