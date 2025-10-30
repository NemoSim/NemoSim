#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model, build_run_config, write_text, write_json
from nemosdk.runner import NemoSimRunner


def main() -> int:
    # Assumed parameters (no user input required)
    out_dir = Path("examples/out/with_energy")
    sim_workdir = Path("bin/Linux")

    # Minimal network
    defaults = BIUNetworkDefaults(VTh=0.6, refractory=12, DSBitWidth=8, DSClockMHz=50)
    layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]
    biu_xml, sup_xml = compile_model(defaults, layers)
    biu_xml_path = out_dir / "biu.xml"
    write_text(biu_xml_path, biu_xml)

    # Use existing CSVs from tests data
    syn_csv = Path("tests/data/multi_layer_test/Spike-in_vs_Not_spike-in.csv")
    neu_csv = Path("tests/data/multi_layer_test/Energy_Neuron_CSV_Content.csv")

    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=biu_xml_path,
        data_input_file=Path("tests/data/multi_layer_test/input.txt"),
        synapses_energy_table_path=syn_csv,
        neuron_energy_table_path=neu_csv,
        relativize_from=sim_workdir,
    )
    cfg_path = out_dir / "config.json"
    write_json(cfg_path, cfg)

    # Always run using assumed simulator location
    runner = NemoSimRunner(working_dir=sim_workdir)
    res = runner.run(cfg_path, check=True)
    print("Return code:", res.returncode)
    print("Logs:", res.stdout_path, res.stderr_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


