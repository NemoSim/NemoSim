#!/usr/bin/env bash

set -euo pipefail

# Run NEMOSIM from the project root while executing the binary in bin/Linux so
# that relative paths inside test config.json files resolve correctly.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BIN_DIR="$PROJECT_ROOT/bin/Linux"
DEFAULT_CONFIG_REL="./Tests/SNN/BIU/config.json"

usage() {
    cat <<EOF
Usage: $(basename "$0") [CONFIG_JSON|TEST_DIR]

Examples:
  $(basename "$0")                 # run default BIU test
  $(basename "$0") bin/Linux/Tests/SNN/BIU/config.json
  $(basename "$0") bin/Linux/Tests/SNN/BIU             # will use its config.json

Notes:
  - The simulator is executed from: $BIN_DIR
  - Relative paths in config are resolved from that directory.
EOF
}

arg="${1:-}" || true

# Determine config path (always resolve to absolute path for invocation)
CONFIG_ABS=""
CONFIG_PATH_REL="$DEFAULT_CONFIG_REL"
if [[ -n "$arg" ]]; then
    # If a directory is provided, assume it contains config.json
    if [[ -d "$PROJECT_ROOT/$arg" ]]; then
        if [[ -f "$PROJECT_ROOT/$arg/config.json" ]]; then
            CONFIG_ABS="$(cd "$PROJECT_ROOT/$arg" && pwd)/config.json"
        else
            echo "Error: '$arg' does not contain a config.json" >&2
            exit 1
        fi
    else
        # Treat as a file path
        # Accept absolute or project-root-relative paths
        if [[ -f "$arg" ]]; then
            CONFIG_ABS="$(cd "$(dirname "$arg")" && pwd)/$(basename "$arg")"
        elif [[ -f "$PROJECT_ROOT/$arg" ]]; then
            CONFIG_ABS="$(cd "$(dirname "$PROJECT_ROOT/$arg")" && pwd)/$(basename "$PROJECT_ROOT/$arg")"
        else
            echo "Error: path '$arg' not found" >&2
            exit 1
        fi
    fi
fi

# Ensure binary exists and is executable
if [[ ! -f "$BIN_DIR/NEMOSIM" ]]; then
    echo "Error: NEMOSIM binary not found at $BIN_DIR/NEMOSIM" >&2
    exit 1
fi
if [[ ! -x "$BIN_DIR/NEMOSIM" ]]; then
    chmod +x "$BIN_DIR/NEMOSIM" || true
fi

# Finalize config arg: prefer absolute resolved path; otherwise default relative
if [[ -z "$CONFIG_ABS" ]]; then
    # default: resolve DEFAULT_CONFIG_REL to absolute
    CONFIG_ABS="$(cd "$BIN_DIR" && cd "$(dirname "$CONFIG_PATH_REL")" && pwd)/$(basename "$CONFIG_PATH_REL")"
fi
CONFIG_ARG="$CONFIG_ABS"

echo "Running NEMOSIM..."
echo "  CWD:        $BIN_DIR"
echo "  Config:     $CONFIG_ARG"
echo

cd "$BIN_DIR"
"$BIN_DIR/NEMOSIM" "$CONFIG_ARG"

