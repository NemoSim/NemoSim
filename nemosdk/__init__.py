"""NemoSDK: Define → Compile → Run BIU spiking networks for NemoSim.

Public API:
- Model: BIUNetworkConfig, Layer, Synapses, NeuronOverrideRange, NeuronOverride
- Compiler: compile_to_xml, build_run_config
- Runner: NemoSimRunner
- CLI: python -m nemosdk.cli

Python >= 3.10
"""

from .model import (
    BIUNetworkDefaults,
    Layer,
    Synapses,
    NeuronOverrideRange,
    NeuronOverride,
)
from .compiler import (
    compile_to_xml,
    compile,
    build_run_config,
)
from .runner import NemoSimRunner, RunResult

__all__ = [
    "BIUNetworkDefaults",
    "Layer",
    "Synapses",
    "NeuronOverrideRange",
    "NeuronOverride",
    "compile_to_xml",
    "compile",
    "build_run_config",
    "NemoSimRunner",
    "RunResult",
]


