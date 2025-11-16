from __future__ import annotations

import json
import os
from pathlib import Path

from nemosdk import cli


def test_cli_build_relativizes_config_paths(tmp_path: Path) -> None:
    out_dir = tmp_path / "artifacts"
    input_file = tmp_path / "input.txt"
    input_file.write_text("0\n", encoding="utf-8")
    sim_workdir = tmp_path / "bin" / "Linux"
    sim_workdir.mkdir(parents=True)

    args = [
        "build",
        str(out_dir),
        str(input_file),
        "--sim-workdir",
        str(sim_workdir),
    ]
    cli.main(args)

    cfg_path = out_dir / "config.json"
    assert cfg_path.exists()
    cfg = json.loads(cfg_path.read_text())

    expected_paths = {
        "output_directory": out_dir / "outputs",
        "xml_config_path": out_dir / "biu.xml",
        "data_input_file": input_file,
    }

    for key, expected in expected_paths.items():
        value = cfg[key]
        assert not os.path.isabs(value), f"{key} should be relative when --sim-workdir is set"
        resolved = (sim_workdir / value).resolve()
        assert resolved == expected.resolve()
