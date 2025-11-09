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
from .probe_utils import watch_probe


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


def _probe_inspect(args: argparse.Namespace) -> None:
    """Inspect probe outputs from a compiled model."""
    compiled = CompiledModel(config_path=Path(args.config))

    if args.list:
        probes = compiled.list_probes()
        if not probes:
            print("No probes found in probes.json")
            return
        print("Available probes:")
        for name in probes:
            try:
                meta = compiled.get_probe_metadata(name)
                layer_index = meta.layer_index
                size = meta.layer_size
            except KeyError:
                layer_index = compiled.get_probe_layer_index(name)
                size = "?"
            print(f"  - {name} (layer {layer_index}, neurons={size})")
        return

    if not args.probe:
        raise SystemExit("--probe is required unless --list is specified")

    probe = compiled.get_probe(args.probe)
    try:
        meta = compiled.get_probe_metadata(args.probe)
        default_neurons = list(range(meta.layer_size))
    except KeyError:
        default_neurons = probe.list_neuron_indices()

    neuron_indices = args.neurons if args.neurons else default_neurons
    if not neuron_indices:
        print("No neuron indices resolved for this probe.")
        return

    signal = args.signal
    getter = {
        "spikes": probe.get_spikes,
        "vin": probe.get_vin,
        "vns": probe.get_vns,
    }[signal]

    if args.follow:
        print(f"Following {signal} for probe '{args.probe}', neurons={neuron_indices} (Ctrl+C to stop)")
        try:
            for neuron_idx in neuron_indices:
                for value in watch_probe(
                    probe,
                    signal,
                    neuron_idx,
                    follow=True,
                    poll_interval=args.poll_interval,
                    max_events=args.max_events,
                ):
                    print(f"[{signal}] neuron {neuron_idx}: {value}")
        except KeyboardInterrupt:
            print("\nStopped following.")
        return

    for neuron_idx in neuron_indices:
        data = getter(neuron_idx)
        if args.head is not None:
            data = data[: args.head]

        if args.summary:
            count = len(data)
            if count == 0:
                print(f"[{signal}] neuron {neuron_idx}: empty")
                continue
            minimum = min(data)
            maximum = max(data)
            average = sum(data) / count
            extra = ""
            if signal == "spikes":
                extra = f", spikes={sum(int(v) for v in data)}"
            print(
                f"[{signal}] neuron {neuron_idx}: count={count}, min={minimum}, max={maximum}, mean={average:.4f}{extra}"
            )
        else:
            print(f"[{signal}] neuron {neuron_idx}: {data}")


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

    p = sub.add_parser("probe", help="Inspect simulation outputs via probe names")
    p.add_argument("config", help="Path to config.json produced by the SDK")
    p.add_argument("--list", action="store_true", help="List available probes and exit")
    p.add_argument("--probe", help="Probe name to inspect")
    p.add_argument("--signal", choices=("spikes", "vin", "vns"), default="spikes")
    p.add_argument("--neurons", type=int, nargs="*", help="Neuron indices to include (defaults to all)")
    p.add_argument("--head", type=int, help="Show only the first N samples")
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics (count/min/max/mean) instead of raw samples",
    )
    p.add_argument(
        "--follow",
        action="store_true",
        help="Tail the signal file(s) until interrupted (like `tail -f`)",
    )
    p.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Polling interval in seconds when --follow is used (default: 0.5)",
    )
    p.add_argument(
        "--max-events",
        type=int,
        help="Optional maximum number of samples to emit when using --follow",
    )
    p.set_defaults(func=_probe_inspect)

    ns = ap.parse_args(argv)
    ns.func(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


