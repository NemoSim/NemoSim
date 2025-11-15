from __future__ import annotations

from pathlib import Path

import pytest

from nemosdk.compiler import compile
from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.runner import NemoSimRunner


ROOT = Path(__file__).resolve().parents[2]
SIM_WORKDIR = ROOT / "bin" / "Linux"
SIM_BINARY = SIM_WORKDIR / "NEMOSIM"


requires_simulator = pytest.mark.skipif(
    not SIM_BINARY.exists(),
    reason="NemoSim binary not found; ensure bin/Linux/NEMOSIM is available for integration tests.",
)


def _assert_any_spike(spikes: list[int]) -> None:
    assert spikes, "Expected spike data."
    assert any(value != 0 for value in spikes), "Expected at least one spike event."


@requires_simulator
def test_build_with_probes_like_example_generates_probe_data(tmp_path: Path) -> None:
    out_dir = tmp_path / "with_probes"

    defaults = BIUNetworkDefaults(
        VTh=0.6,
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )

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
        probe="input",
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
        probe="output",
    )

    data_input_file = ROOT / "tests" / "data" / "multi_layer_test" / "input.txt"

    compiled_model = compile(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        data_input_file=data_input_file,
    )

    runner = NemoSimRunner(working_dir=SIM_WORKDIR)
    result = runner.run(compiled_model, check=True)
    assert result.returncode == 0

    input_probe = compiled_model.get_probe("input")
    _assert_any_spike(input_probe.get_spikes(0))
    output_probe = compiled_model.get_probe("output")
    output_spikes = output_probe.get_spikes(0)
    _assert_any_spike(output_spikes)
    vin = output_probe.get_vin(0)
    assert vin, "Expected vin samples."
    assert len(vin) == len(output_spikes)


@requires_simulator
def test_build_with_inline_input_like_example_spikes(tmp_path: Path) -> None:
    out_dir = tmp_path / "with_inline_input"

    defaults = BIUNetworkDefaults(
        VTh=0.05,
        RLeak=500e6,
        refractory=12,
        DSBitWidth=4,
        DSClockMHz=10,
    )

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
        synapses=Synapses(rows=1, cols=5, weights=[[3.0, 3.0, 3.0, 3.0, 3.0]]),
        probe="output",
    )

    samples = [
        (1, 6, 6, 1, 6),
        (6, 1, 12, 11, 6),
        (1, 0, 11, 6, 5),
        (0, 11, 10, 5, 0),
        (6, 5, 0, 0, 0),
    ]

    compiled_model = compile(
        defaults=defaults,
        layers=[layer0, layer1],
        include_supervisor=True,
        out_dir=out_dir,
        input_data=samples,
    )

    runner = NemoSimRunner(working_dir=SIM_WORKDIR)
    result = runner.run(compiled_model, check=True)
    assert result.returncode == 0

    input_probe = compiled_model.get_probe("inputs")
    spike_totals = [sum(input_probe.get_spikes(idx)) for idx in input_probe.list_neuron_indices()]
    assert any(total > 0 for total in spike_totals), "Expected at least one active input neuron."

    output_probe = compiled_model.get_probe("output")
    _assert_any_spike(output_probe.get_spikes(0))
    vns = output_probe.get_vns(0)
    assert vns, "Expected vns samples."

