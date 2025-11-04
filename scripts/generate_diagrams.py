#!/usr/bin/env python3
"""Generate class diagrams for NemoSDK using pyreverse.

This script provides a convenient way to generate UML class diagrams
from the NemoSDK Python codebase.

Usage:
    python scripts/generate_diagrams.py
    python scripts/generate_diagrams.py --format png --output docs/diagrams
    python scripts/generate_diagrams.py --format dot
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def check_pyreverse() -> bool:
    """Check if pyreverse is available."""
    try:
        result = subprocess.run(
            ["pyreverse", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def generate_diagrams(
    output_format: str = "png",
    output_dir: Path | None = None,
    project_name: str = "NemoSDK",
) -> int:
    """Generate class diagrams using pyreverse."""
    if not check_pyreverse():
        print("Error: pyreverse not found. Install it with: pip install pylint")
        return 1

    if output_dir is None:
        output_dir = Path("docs/diagrams")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    nemosdk_path = Path("nemosdk")
    if not nemosdk_path.exists():
        print(f"Error: {nemosdk_path} directory not found. Run from project root.")
        return 1

    # Generate class diagram
    cmd = [
        "pyreverse",
        "-o",
        output_format,
        "-p",
        project_name,
        str(nemosdk_path),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path.cwd(), check=False)

    if result.returncode != 0:
        print("Error: pyreverse failed")
        return result.returncode

    # Move generated files to output directory if using png
    if output_format == "png":
        for pattern in ["classes_*.png", "packages_*.png"]:
            for file in Path(".").glob(pattern):
                new_path = output_dir / file.name
                file.rename(new_path)
                print(f"Generated: {new_path}")
    elif output_format == "dot":
        for pattern in ["classes_*.dot", "packages_*.dot"]:
            for file in Path(".").glob(pattern):
                new_path = output_dir / file.name
                file.rename(new_path)
                print(f"Generated: {new_path}")
        print("\nTo convert DOT to PNG, run:")
        print(f"  dot -Tpng {output_dir}/classes_{project_name}.dot -o {output_dir}/class_diagram.png")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate UML class diagrams for NemoSDK"
    )
    parser.add_argument(
        "--format",
        choices=["png", "dot", "svg"],
        default="png",
        help="Output format (default: png)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/diagrams"),
        help="Output directory (default: docs/diagrams)",
    )
    parser.add_argument(
        "--project",
        default="NemoSDK",
        help="Project name for diagram (default: NemoSDK)",
    )

    args = parser.parse_args()
    return generate_diagrams(
        output_format=args.format,
        output_dir=args.output,
        project_name=args.project,
    )


if __name__ == "__main__":
    raise SystemExit(main())
