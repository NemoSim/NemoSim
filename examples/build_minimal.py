#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def main() -> int:
    # Assumed parameters (no user input required)
    out_dir = Path("examples/out/minimal")
    sim_workdir = Path("bin/Linux")

    defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
    layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]

    # Two lines: compile, then run
    cfg_path = compile_model(
        defaults=defaults,
        layers=layers,
        out_dir=out_dir,
        data_input_file=Path("tests/data/multi_layer_test/input.txt"),
        relativize_from=sim_workdir,
    )
    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(cfg_path, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


