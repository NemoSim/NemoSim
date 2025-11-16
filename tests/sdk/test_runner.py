from __future__ import annotations

from pathlib import Path
import os

from nemosdk.runner import NemoSimRunner
from nemosdk.compiler import CompiledModel


def _make_dummy_binary(dir_path: Path) -> Path:
    bin_path = dir_path / "NEMOSIM"
    bin_path.write_text("#!/usr/bin/env bash\necho 'Finished executing.'\n", encoding="utf-8")
    os.chmod(bin_path, 0o755)
    return bin_path


def _make_custom_binary(dir_path: Path, name: str, script_body: str) -> Path:
    bin_path = dir_path / name
    bin_path.write_text(
        "#!/usr/bin/env bash\nset -e\n"
        f"{script_body}\n",
        encoding="utf-8",
    )
    os.chmod(bin_path, 0o755)
    return bin_path


def test_runner_success_captures_logs(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_dummy_binary(work)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    res = runner.run(CompiledModel(config_path=cfg), check=True)
    assert res.returncode == 0
    assert res.stdout_path.exists()
    assert res.stderr_path.exists()


def test_runner_missing_binary_error(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    try:
        runner.run(CompiledModel(config_path=cfg))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_runner_env_var_binary_path(tmp_path: Path):
    """Test that NEMOSIM_BINARY environment variable overrides default binary path."""
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    custom_bin_dir = tmp_path / "custom_bin"
    custom_bin_dir.mkdir(parents=True)
    custom_binary = custom_bin_dir / "CUSTOM_NEMOSIM"
    custom_binary.write_text("#!/usr/bin/env bash\necho 'Finished executing.'\n", encoding="utf-8")
    os.chmod(custom_binary, 0o755)
    
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    # Set environment variable
    os.environ["NEMOSIM_BINARY"] = str(custom_binary)
    try:
        runner = NemoSimRunner(working_dir=work)
        assert runner.binary_path == custom_binary
        res = runner.run(CompiledModel(config_path=cfg), check=True)
        assert res.returncode == 0
    finally:
        # Clean up environment variable
        os.environ.pop("NEMOSIM_BINARY", None)


def test_runner_explicit_binary_overrides_env_var(tmp_path: Path):
    """Test that explicit binary_path parameter takes precedence over environment variable."""
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    explicit_binary = work / "EXPLICIT_NEMOSIM"
    explicit_binary.write_text("#!/usr/bin/env bash\necho 'Finished executing.'\n", encoding="utf-8")
    os.chmod(explicit_binary, 0o755)
    
    env_binary = tmp_path / "env_binary"
    env_binary.write_text("#!/usr/bin/env bash\necho 'Should not use this'\n", encoding="utf-8")
    os.chmod(env_binary, 0o755)
    
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    # Set environment variable
    os.environ["NEMOSIM_BINARY"] = str(env_binary)
    try:
        runner = NemoSimRunner(working_dir=work, binary_path=explicit_binary)
        assert runner.binary_path == explicit_binary
        res = runner.run(CompiledModel(config_path=cfg), check=True)
        assert res.returncode == 0
    finally:
        # Clean up environment variable
        os.environ.pop("NEMOSIM_BINARY", None)


def test_runner_timeout(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_custom_binary(work, "NEMOSIM", "sleep 2")
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    try:
        runner.run(CompiledModel(config_path=cfg), timeout=0.1)
        assert False, "Expected TimeoutError"
    except TimeoutError:
        pass


def test_runner_stream_output(tmp_path: Path, capsys):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_custom_binary(
        work,
        "NEMOSIM",
        "echo 'stdout line'\necho 'stderr line' >&2",
    )
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    runner = NemoSimRunner(working_dir=work)
    res = runner.run(
        CompiledModel(config_path=cfg),
        stream_output=True,
        stdout_callback=stdout_lines.append,
        stderr_callback=stderr_lines.append,
        check=True,
    )

    assert res.returncode == 0
    captured = capsys.readouterr()
    assert "stdout line" in captured.out
    assert "stderr line" in captured.err
    assert any("stdout line" in line for line in stdout_lines)
    assert any("stderr line" in line for line in stderr_lines)


def test_runner_log_files_unique(tmp_path: Path):
    work = tmp_path / "Linux"
    work.mkdir(parents=True)
    _make_dummy_binary(work)
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")

    runner = NemoSimRunner(working_dir=work)
    compiled = CompiledModel(config_path=cfg)

    res1 = runner.run(compiled, check=True)
    res2 = runner.run(compiled, check=True)

    assert res1.stdout_path != res2.stdout_path
    assert res1.stderr_path != res2.stderr_path

