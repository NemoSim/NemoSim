#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses, NeuronOverrideRange, NeuronOverride
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def main() -> int:
    # Assumed parameters (no user input required)
    out_dir = Path("examples/out/multilayer_precedence")
    sim_workdir = Path("bin/Linux")

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
        ranges=[NeuronOverrideRange(start=0, end=2, VTh=0.5, RLeak=550e6, refractory=10)],
        neurons=[NeuronOverride(index=1, VTh=0.7)],
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
        ranges=[
            NeuronOverrideRange(start=0, end=3, VTh=0.2),
            NeuronOverrideRange(start=4, end=6, VTh=0.2, RLeak=520e6, refractory=12),
        ],
        neurons=[NeuronOverride(index=6, VTh=0.19)],
    )

    # Two lines: compile, then run
    cfg_path = compile_model(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
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


