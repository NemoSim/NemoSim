from __future__ import annotations

import pytest
from nemosdk.model import (
    BIUNetworkDefaults,
    Layer,
    Synapses,
    NeuronOverride,
    NeuronOverrideRange,
)
from nemosdk.compiler import compile as compile_model


def test_invalid_ds_bitwidth_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=16, DSClockMHz=10)
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]))
    with pytest.raises(ValueError):
        compile_model(defaults, [layer])


def test_non_positive_ds_clock_raises():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=0)
    layer = Layer(size=1, synapses=Synapses(rows=1, cols=1, weights=[[1.0]]))
    with pytest.raises(ValueError):
        compile_model(defaults, [layer])


def test_synapse_rows_cols_must_match():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=1)
    # rows=2 but only 1 row provided
    bad_syn = Synapses(rows=2, cols=1, weights=[[1.0]])
    layer = Layer(size=2, synapses=bad_syn)
    with pytest.raises(ValueError):
        layer.validate()


def test_layer_size_equals_synapse_rows():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=1)
    syn = Synapses(rows=1, cols=1, weights=[[1.0]])
    layer = Layer(size=2, synapses=syn)
    with pytest.raises(ValueError):
        compile_model(defaults, [layer])


def test_override_indices_out_of_bounds():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=1)
    syn = Synapses(rows=1, cols=1, weights=[[1.0]])
    # neuron index out of bounds
    layer = Layer(size=1, synapses=syn, neurons=[NeuronOverride(index=3, VTh=0.2)])
    with pytest.raises(ValueError):
        layer.validate()


def test_range_out_of_bounds():
    defaults = BIUNetworkDefaults(DSBitWidth=4, DSClockMHz=1)
    syn = Synapses(rows=2, cols=1, weights=[[1.0], [2.0]])
    # end >= size
    layer = Layer(size=2, synapses=syn, ranges=[NeuronOverrideRange(start=0, end=2, VTh=0.2)])
    with pytest.raises(ValueError):
        layer.validate()



