from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence
import subprocess
import datetime as _dt

try:
    from .compiler import CompiledModel
except Exception:  # pragma: no cover - avoid import cycles during type checking
    CompiledModel = None  # type: ignore


@dataclass(slots=True)
class RunResult:
    """Immutable result summary for a simulator invocation."""
    returncode: int
    command: List[str]
    cwd: Path
    stdout_path: Path
    stderr_path: Path


class NemoSimRunner:
    """Runner for the NemoSim binary with logging and path handling.

    - `working_dir` should be the simulator working directory (e.g., `bin/Linux`).
    - `binary_path` defaults to `working_dir / "NEMOSIM"` when not provided.
    - Logs are written under `working_dir/logs` with timestamped filenames.
    """

    def __init__(self, working_dir: Path, binary_path: Optional[Path] = None):
        self.working_dir = working_dir
        self.binary_path = binary_path or (working_dir / "NEMOSIM")

    def run(
        self,
        compiled: "CompiledModel",
        *,
        extra_args: Optional[Sequence[str]] = None,
        logs_dir: Optional[Path] = None,
        check: bool = True,
    ) -> RunResult:
        """Execute the simulator with the provided compiled model.

        - `compiled` must expose `.get_config_path()` (see `CompiledModel`).
        - `extra_args` are appended to the command line.
        - When `check=True`, a non‑zero exit raises `RuntimeError` with log paths.
        """
        config_path = compiled.get_config_path().resolve()
        if not self.working_dir.exists():
            raise FileNotFoundError(f"Invalid working directory: {self.working_dir}")
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Simulator binary not found: {self.binary_path}")
        if not self.binary_path.is_file():
            raise FileNotFoundError(f"Simulator binary is not a file: {self.binary_path}")

        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = logs_dir or (self.working_dir / "logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = logs_dir / f"nemosim_stdout_{ts}.log"
        stderr_path = logs_dir / f"nemosim_stderr_{ts}.log"

        # Use a path to the binary that's valid after chdir into working_dir
        if Path(self.binary_path).is_absolute():
            bin_arg = str(self.binary_path)
        else:
            bin_arg = "./" + Path(self.binary_path).name
        args: List[str] = [bin_arg, str(config_path)]
        if extra_args:
            args.extend(list(extra_args))

        with stdout_path.open("w", encoding="utf-8") as out_fh, stderr_path.open("w", encoding="utf-8") as err_fh:
            proc = subprocess.run(
                args,
                cwd=str(self.working_dir),
                stdout=out_fh,
                stderr=err_fh,
                text=True,
                check=False,
            )

        result = RunResult(
            returncode=proc.returncode,
            command=args,
            cwd=self.working_dir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(
                f"Simulator exited with code {proc.returncode}. See logs: {stdout_path}, {stderr_path}"
            )
        return result


