from __future__ import annotations

from pathlib import Path
import pytest

from nemosdk.runner import NemoSimRunner
from nemosdk.compiler import CompiledModel


def test_runner_missing_workdir_raises():
    runner = NemoSimRunner(working_dir=Path("/path/does/not/exist"))
    with pytest.raises(FileNotFoundError):
        runner.run(CompiledModel(config_path=Path("config.json")))



