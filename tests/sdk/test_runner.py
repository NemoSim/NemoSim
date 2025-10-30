from __future__ import annotations

from pathlib import Path
import os

from nemosdk.runner import NemoSimRunner
from nemosdk.compiler import CompiledModel


def _make_dummy_binary(dir_path: Path) -> Path:
    bin_path = dir_path / "NEMOSIM"
    bin_path.write_text("#!/usr/bin/env bash\necho 'Finished executing.'\n", encoding="utf-8")
    os.chmod(bin_path, 0o755)
    return bin_path


def test_runner_success_captures_logs(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_dummy_binary(work)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    res = runner.run(CompiledModel(config_path=cfg), check=True)
    assert res.returncode == 0
    assert res.stdout_path.exists()
    assert res.stderr_path.exists()


def test_runner_missing_binary_error(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    try:
        runner.run(CompiledModel(config_path=cfg))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass



