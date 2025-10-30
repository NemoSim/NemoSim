#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses
from nemosdk.compiler import compile as compile_model, build_run_config, write_text, write_json
from nemosdk.runner import NemoSimRunner


def make_layers():
    return [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]


def build_one(out_dir: Path, sim_workdir: Path, defaults: BIUNetworkDefaults, name: str, run: bool):
    layers = make_layers()
    biu_xml, sup_xml = compile_model(defaults, layers)
    biu_xml_path = out_dir / name / "biu.xml"
    write_text(biu_xml_path, biu_xml)
    cfg = build_run_config(
        output_directory=out_dir / name / "output",
        xml_config_path=biu_xml_path,
        data_input_file=Path("tests/data/multi_layer_test/input.txt"),
        relativize_from=sim_workdir,
    )
    cfg_path = out_dir / name / "config.json"
    write_json(cfg_path, cfg)
    if run:
        runner = NemoSimRunner(working_dir=sim_workdir)
        res = runner.run(cfg_path, check=True)
        print(f"[{name}] return code:", res.returncode)


def main() -> int:
    # Assumed parameters (no user input required)
    out_dir = Path("examples/out/ds_variants")
    sim_workdir = Path("bin/Linux")

    # 1) Explicit ThresholdMode
    d1 = BIUNetworkDefaults(VTh=0.9, DSBitWidth=4, DSClockMHz=10, DSMode="ThresholdMode")
    build_one(out_dir, sim_workdir, d1, "threshold_mode", True)

    # 2) Missing DSMode -> defaults to ThresholdMode
    d2 = BIUNetworkDefaults(VTh=0.9, DSBitWidth=8, DSClockMHz=25, DSMode=None)
    build_one(out_dir, sim_workdir, d2, "defaulted_mode", True)

    # 3) FrequencyMode
    d3 = BIUNetworkDefaults(VTh=0.9, DSBitWidth=8, DSClockMHz=50, DSMode="FrequencyMode")
    build_one(out_dir, sim_workdir, d3, "frequency_mode", True)

    print("Artifacts written under:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


