from __future__ import annotations

"""NemoSDK CLI: build minimal artifacts, run the simulator, or diagnose paths.

Subcommands:
  - build: compile a minimal 1×1 network and write artifacts
  - run:   run the simulator with a given config.json
  - diag:  print how a path resolves from the simulator working dir
"""

import argparse
from pathlib import Path
import sys

from .compiler import compile as compile_model, build_run_config, write_text, write_json, CompiledModel
from .model import BIUNetworkDefaults, Layer, Synapses
from .runner import NemoSimRunner


def _write_artifacts(args: argparse.Namespace) -> None:
    """Build a minimal 1×1 network and write BIU XML, optional supervisor, and config.json."""
    defaults = BIUNetworkDefaults(
        VTh=args.vth,
        RLeak=args.rleak,
        refractory=args.refractory,
        DSBitWidth=args.ds_bitwidth,
        DSClockMHz=args.ds_clock_mhz,
        DSMode=args.ds_mode,
    )
    layers = [
        Layer(
            size=1,
            synapses=Synapses(rows=1, cols=1, weights=[[args.weight]]),
        )
    ]
    biu_xml, sup_xml = compile_model(
        defaults, layers, include_supervisor=args.include_supervisor
    )

    out_dir = Path(args.output_dir)
    biu_xml_path = out_dir / "biu.xml"
    write_text(biu_xml_path, biu_xml)
    sup_xml_path = None
    if sup_xml is not None:
        sup_xml_path = out_dir / "supervisor.xml"
        write_text(sup_xml_path, sup_xml)

    # Build config.json with absolute paths
    cfg = build_run_config(
        output_directory=out_dir / "outputs",
        xml_config_path=biu_xml_path,
        data_input_file=Path(args.data_input_file),
        sup_xml_config_path=sup_xml_path,
        synapses_energy_table_path=Path(args.syn_energy) if args.syn_energy else None,
        neuron_energy_table_path=Path(args.neu_energy) if args.neu_energy else None,
    )
    write_json(out_dir / "config.json", cfg)


def _run_sim(args: argparse.Namespace) -> None:
    """Run the simulator using a config.json path and print basic results/log paths."""
    runner = NemoSimRunner(working_dir=Path(args.sim_workdir), binary_path=Path(args.bin) if args.bin else None)
    compiled = CompiledModel(config_path=Path(args.config))
    res = runner.run(compiled, extra_args=args.extra)
    print("Return code:", res.returncode)
    print("Stdout log:", res.stdout_path)
    print("Stderr log:", res.stderr_path)


def _diag(args: argparse.Namespace) -> None:
    """Echo a path as seen from the simulator working directory."""
    base = Path(args.sim_workdir)
    p = Path(args.path)
    if p.is_absolute():
        print(p)
    else:
        print(base / p)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nemosdk", description="NemoSDK CLI: build/compile/run/diagnose")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Compile minimal network and write artifacts")
    b.add_argument("output_dir", help="Directory to write artifacts")
    b.add_argument("data_input_file", help="Path to input.txt or similar data file")
    b.add_argument("--sim-workdir", help="Simulator working dir (e.g., bin/Linux)")
    b.add_argument("--include-supervisor", action="store_true", help="Emit supervisor.xml as well")
    b.add_argument("--weight", type=float, default=7.0)
    b.add_argument("--vth", type=float)
    b.add_argument("--rleak", type=float)
    b.add_argument("--refractory", type=int)
    b.add_argument("--ds-bitwidth", type=int)
    b.add_argument("--ds-clock-mhz", type=float)
    b.add_argument("--ds-mode", type=str)
    b.add_argument("--syn-energy", help="Synapses energy table CSV path")
    b.add_argument("--neu-energy", help="Neuron energy table CSV path")
    b.set_defaults(func=_write_artifacts)

    r = sub.add_parser("run", help="Run simulator with config.json")
    r.add_argument("config", help="config.json path")
    r.add_argument("--sim-workdir", required=True, help="Simulator working dir (e.g., bin/Linux)")
    r.add_argument("--bin", help="Override simulator binary path")
    r.add_argument("extra", nargs=argparse.REMAINDER, help="Extra args passed to simulator")
    r.set_defaults(func=_run_sim)

    d = sub.add_parser("diag", help="Print how a path resolves from simulator working dir")
    d.add_argument("--sim-workdir", required=True)
    d.add_argument("path")
    d.set_defaults(func=_diag)

    ns = ap.parse_args(argv)
    ns.func(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


