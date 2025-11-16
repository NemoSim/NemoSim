from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_readme_file_exists() -> None:
    """Ensure the readme referenced in pyproject.toml exists on disk."""
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^readme\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert match, "readme field not found in pyproject.toml"
    readme_path = pyproject.parent / match.group(1)
    assert readme_path.exists(), f"Referenced readme does not exist: {readme_path}"
