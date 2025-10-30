from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
import json

from nemosdk.model import BIUNetworkDefaults, Layer, Synapses, NeuronOverride, NeuronOverrideRange
from nemosdk.compiler import compile as compile_model, build_run_config


def test_compile_minimal_xml_roundtrip(tmp_path: Path):
    defaults = BIUNetworkDefaults(VTh=0.9, refractory=14, DSBitWidth=8, DSClockMHz=50)
    layers = [Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[7.0]]))]

    xml_str, sup = compile_model(defaults, layers)
    assert sup is None
    # Parse to ensure well-formed and expected root/attrs
    root = ET.fromstring(xml_str)
    assert root.tag == "NetworkConfig"
    assert root.attrib.get("type") == "BIUNetwork"
    biu = root.find("BIUNetwork")
    assert biu is not None
    assert biu.findtext("VTh") == "0.9"
    assert biu.findtext("refractory") == "14"
    assert biu.findtext("DSBitWidth") == "8"
    assert biu.findtext("DSClockMHz") == "50"
    # DSMode defaults to ThresholdMode if missing
    assert biu.findtext("DSMode") == "ThresholdMode"
    arch = root.find("Architecture")
    assert arch is not None and arch.find("Layer") is not None


def test_precedence_and_validation(tmp_path: Path):
    defaults = BIUNetworkDefaults(VTh=0.6, RLeak=500e6, refractory=12, DSBitWidth=4, DSClockMHz=10)
    layer = Layer(
        size=3,
        synapses=Synapses(rows=3, cols=2, weights=[[1, 2], [3, 4], [5, 6]]),
        ranges=[NeuronOverrideRange(start=0, end=2, VTh=0.5, RLeak=550e6, refractory=10)],
        neurons=[NeuronOverride(index=1, VTh=0.7)],
    )

    xml_str, _ = compile_model(defaults, [layer])
    root = ET.fromstring(xml_str)
    lyr = root.find("Architecture/Layer")
    assert lyr is not None
    # Ensure rows emitted and counts match
    rows = [r.text.strip() for r in lyr.findall("synapses/weights/row")]
    assert len(rows) == 3
    # Ensure overrides exist
    assert lyr.find("NeuronRange") is not None
    assert lyr.find("Neuron[@index='1']") is not None


def test_build_run_config_relativize(tmp_path: Path):
    base = tmp_path / "bin" / "Linux"
    base.mkdir(parents=True)
    out_dir = tmp_path / "scenario"
    xml = out_dir / "biu.xml"
    data = tmp_path / "data" / "input.txt"
    xml.parent.mkdir(parents=True)
    xml.write_text("<x/>")
    data.parent.mkdir(parents=True)
    data.write_text("0\n")

    cfg = build_run_config(
        output_directory=out_dir / "output",
        xml_config_path=xml,
        data_input_file=data,
        sup_xml_config_path=None,
        relativize_from=base,
    )
    # All values should be strings relative to base
    assert cfg["xml_config_path"].startswith("../../")
    assert cfg["output_directory"].startswith("../../")
    assert cfg["data_input_file"].startswith("../") or cfg["data_input_file"].startswith("../../")


