#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running: build_minimal"
python examples/build_minimal.py --run

echo "Running: build_multilayer_precedence"
python examples/build_multilayer_precedence.py --run

echo "Running: build_ds_variants"
python examples/build_ds_variants.py --run

echo "Running: build_with_energy_tables"
python examples/build_with_energy_tables.py --run

echo "All example runs completed."


