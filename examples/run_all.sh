#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Running: build_minimal"
python examples/build_minimal.py

echo "Running: build_multilayer_precedence"
python examples/build_multilayer_precedence.py

echo "Running: build_ds_variants"
python examples/build_ds_variants.py

echo "Running: build_with_energy_tables"
python examples/build_with_energy_tables.py

echo "Running: build_with_plotting"
python examples/build_with_plotting.py

echo "All example runs completed."


