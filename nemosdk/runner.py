from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional, Sequence
import datetime as _dt
import os
import subprocess
import sys
import threading

try:
    from .compiler import CompiledModel
except Exception:  # pragma: no cover - avoid import cycles during type checking
    CompiledModel = None  # type: ignore


@dataclass(slots=True)
class RunResult:
    """Immutable result summary for a simulator invocation.
    
    Attributes:
        returncode: Process exit code (0 = success, non-zero = failure)
        command: Full command line that was executed
        cwd: Working directory where the command was executed
        stdout_path: Path to the stdout log file
        stderr_path: Path to the stderr log file (contains error details if returncode != 0)
    """
    returncode: int
    command: List[str]
    cwd: Path
    stdout_path: Path
    stderr_path: Path
    
    @property
    def is_success(self) -> bool:
        """Returns True if the simulation completed successfully (returncode == 0)."""
        return self.returncode == 0


class NemoSimRunner:
    """Runner for the NemoSim binary with logging and path handling.

    - `working_dir` should be the simulator working directory (e.g., `bin/Linux`).
    - `binary_path` defaults to `working_dir / "NEMOSIM"` when not provided.
      Can be overridden via the `NEMOSIM_BINARY` environment variable.
    - Logs are written under `working_dir/logs` with timestamped filenames.
    """

    def __init__(self, working_dir: Path, binary_path: Optional[Path] = None):
        self.working_dir = working_dir
        if binary_path is not None:
            self.binary_path = binary_path
        elif os.getenv("NEMOSIM_BINARY"):
            self.binary_path = Path(os.getenv("NEMOSIM_BINARY"))
        else:
            self.binary_path = working_dir / "NEMOSIM"

    def run(
        self,
        compiled: "CompiledModel",
        *,
        extra_args: Optional[Sequence[str]] = None,
        logs_dir: Optional[Path] = None,
        check: bool = True,
        timeout: Optional[float] = None,
        env: Optional[Mapping[str, str]] = None,
        stream_output: bool = False,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> RunResult:
        """Execute the simulator with the provided compiled model.

        Args:
            compiled: Must expose `.get_config_path()` (see `CompiledModel`).
            extra_args: Optional additional arguments appended to the command line.
            logs_dir: Directory for log files (defaults to `working_dir/logs`).
            check: If True, raises `RuntimeError` when return code is non-zero.
            timeout: Optional timeout (seconds). When exceeded, the simulator is terminated and `TimeoutError` is raised.
            env: Optional mapping of environment variables to provide to the simulator.
            stream_output: When True, mirror stdout/stderr to the current process streams while still writing logs.
            stdout_callback: Optional callable invoked with each stdout line (newline preserved) when streaming.
            stderr_callback: Optional callable invoked with each stderr line (newline preserved) when streaming.

        Returns:
            RunResult with return code and log file paths.

        Raises:
            FileNotFoundError: If working directory or binary doesn't exist.
            RuntimeError: If `check=True` and simulator exits with non-zero code.
            TimeoutError: If the simulator exceeds the provided timeout.
            
        Note:
            Return codes follow standard process exit codes:
            - 0 = Success
            - Non-zero = Failure (error details in stderr log)
        """
        config_path = compiled.get_config_path().resolve()
        if not self.working_dir.exists():
            raise FileNotFoundError(f"Invalid working directory: {self.working_dir}")
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Simulator binary not found: {self.binary_path}")
        if not self.binary_path.is_file():
            raise FileNotFoundError(f"Simulator binary is not a file: {self.binary_path}")

        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        logs_dir = logs_dir or (self.working_dir / "logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = logs_dir / f"nemosim_stdout_{ts}.log"
        stderr_path = logs_dir / f"nemosim_stderr_{ts}.log"

        mirror_stdout = stream_output or stdout_callback is not None
        mirror_stderr = stream_output or stderr_callback is not None

        # Use a path to the binary that's valid after chdir into working_dir
        if Path(self.binary_path).is_absolute():
            bin_arg = str(self.binary_path)
        else:
            bin_arg = "./" + Path(self.binary_path).name
        args: List[str] = [bin_arg, str(config_path)]
        if extra_args:
            args.extend(list(extra_args))

        with stdout_path.open("w", encoding="utf-8") as out_fh, stderr_path.open("w", encoding="utf-8") as err_fh:
            if not mirror_stdout and not mirror_stderr:
                try:
                    proc = subprocess.run(
                        args,
                        cwd=str(self.working_dir),
                        stdout=out_fh,
                        stderr=err_fh,
                        text=True,
                        check=False,
                        timeout=timeout,
                        env=dict(env) if env is not None else None,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise TimeoutError(
                        f"Simulator timed out after {timeout} seconds. See logs: {stdout_path}, {stderr_path}"
                    ) from exc
            else:
                proc = subprocess.Popen(
                    args,
                    cwd=str(self.working_dir),
                    stdout=subprocess.PIPE if mirror_stdout else out_fh,
                    stderr=subprocess.PIPE if mirror_stderr else err_fh,
                    text=True,
                    env=dict(env) if env is not None else None,
                )

                threads: list[threading.Thread] = []

                def _make_forwarder(
                    stream,
                    log_file,
                    *,
                    callback: Optional[Callable[[str], None]],
                    mirror_to: Optional[Callable[[str], None]],
                ):
                    def _forward() -> None:
                        try:
                            for line in iter(stream.readline, ""):
                                log_file.write(line)
                                log_file.flush()
                                if callback is not None:
                                    callback(line)
                                if mirror_to is not None:
                                    mirror_to(line)
                        finally:
                            stream.close()

                    return _forward

                if mirror_stdout and proc.stdout is not None:
                    stdout_forward = _make_forwarder(
                        proc.stdout,
                        out_fh,
                        callback=stdout_callback,
                        mirror_to=_build_mirror_fn(stream_output, sys.stdout),
                    )
                    threads.append(threading.Thread(target=stdout_forward, daemon=True))

                if mirror_stderr and proc.stderr is not None:
                    stderr_forward = _make_forwarder(
                        proc.stderr,
                        err_fh,
                        callback=stderr_callback,
                        mirror_to=_build_mirror_fn(stream_output, sys.stderr),
                    )
                    threads.append(threading.Thread(target=stderr_forward, daemon=True))

                for thread in threads:
                    thread.start()

                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired as exc:
                    proc.kill()
                    proc.wait()
                    raise TimeoutError(
                        f"Simulator timed out after {timeout} seconds. See logs: {stdout_path}, {stderr_path}"
                    ) from exc
                finally:
                    for thread in threads:
                        thread.join()

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


def _build_mirror_fn(stream_output: bool, target_stream) -> Optional[Callable[[str], None]]:
    if not stream_output:
        return None

    def _mirror(line: str) -> None:
        target_stream.write(line)
        target_stream.flush()

    return _mirror

