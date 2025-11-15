#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model
from nemosdk.runner import NemoSimRunner


def main() -> int:
    """Build and run a small network using in-memory input samples."""
    out_dir = Path("examples/out/with_inline_input")
    sim_workdir = Path("bin/Linux")

    defaults = BIUNetworkDefaults(
        VTh=0.05,
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )

    # First layer has five neurons and consumes five distinct input channels.
    # Each neuron is wired to a unique column via an identity-matrix synapse.
    layer0 = Layer(
        size=5,
        synapses=Synapses(
            rows=5,
            cols=5,
            weights=[
                [6.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 5.5, 0.0, 0.0, 0.0],
                [0.0, 0.0, 5.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 4.5, 0.0],
                [0.0, 0.0, 0.0, 0.0, 4.0],
            ],
        ),
        probe="inputs",
    )
    layer1 = Layer(
        size=1,
        synapses=Synapses(
            rows=1,
            cols=5,
            weights=[[3.0, 3.0, 3.0, 3.0, 3.0]],
        ),
        probe="output",
    )

    # Provide stimulus inline (no input.txt on disk required).
    # These numbers are written into out_dir/input.txt automatically.
    samples = [
        (1, 6, 6, 1, 6),
        (6, 1, 12, 11, 6),
        (1, 0, 11, 6, 5),
        (0, 11, 10, 5, 0),
        (6, 5, 0, 0, 0),
    ]

    compiled = compile_model(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        input_data=samples,
    )

    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(compiled, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)

    input_probe = compiled.get_probe("inputs")
    output_probe = compiled.get_probe("output")
    for neuron in input_probe.list_neuron_indices():
        try:
            spikes = input_probe.get_spikes(neuron)
            print(f"Layer0 neuron {neuron} spikes:", sum(spikes))
        except FileNotFoundError:
            print(f"Layer0 neuron {neuron} spikes: <no data>")
    try:
        out_spikes = output_probe.get_spikes(0)
        print("Output spikes:", sum(out_spikes))
    except FileNotFoundError:
        print("Output spikes: <no data>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
