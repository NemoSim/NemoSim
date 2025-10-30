import os
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "run_nemosim.sh"
BIU_DIR = PROJECT_ROOT / "bin" / "Linux" / "Tests" / "SNN" / "BIU"
BIU_CONFIG = BIU_DIR / "config.json"

# New scenarios under BIU dir
MULTI_DIR = BIU_DIR / "multi_layer_test"
MULTI_CONFIG = MULTI_DIR / "config.json"
MULTI_OUTPUT = MULTI_DIR / "output"

PRECEDENCE_DIR = BIU_DIR / "per_neuron_precedence_test"
PRECEDENCE_CONFIG = PRECEDENCE_DIR / "config.json"
PRECEDENCE_OUTPUT = PRECEDENCE_DIR / "output"

# Root-level test data (moved under tests/data)
ROOT_MULTI_DIR = PROJECT_ROOT / "tests" / "data" / "multi_layer_test"
ROOT_MULTI_CONFIG = ROOT_MULTI_DIR / "config.json"
ROOT_MULTI_OUTPUT = ROOT_MULTI_DIR / "output"

ROOT_PRECEDENCE_DIR = PROJECT_ROOT / "tests" / "data" / "per_neuron_precedence_test"
ROOT_PRECEDENCE_CONFIG = ROOT_PRECEDENCE_DIR / "config.json"
ROOT_PRECEDENCE_OUTPUT = ROOT_PRECEDENCE_DIR / "output"

ROOT_ML_OVERRIDES_DIR = PROJECT_ROOT / "tests" / "data" / "multi_layer_overrides_test"
ROOT_ML_OVERRIDES_CONFIG = ROOT_ML_OVERRIDES_DIR / "config.json"
ROOT_ML_OVERRIDES_OUTPUT = ROOT_ML_OVERRIDES_DIR / "output"


def run_and_capture(args):
    env = os.environ.copy()
    proc = subprocess.run(
        args,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


def extract_totals(output: str):
    total_syn = None
    total_neu = None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Total synaptic energy:"):
            total_syn = line.split(":", 1)[1].strip()
        elif line.startswith("Total neurons energy:"):
            total_neu = line.split(":", 1)[1].strip()
    return total_syn, total_neu


class TestNemoSimRunner(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), f"Missing script: {SCRIPT}")
        self.assertTrue(os.access(SCRIPT, os.X_OK), f"Script not executable: {SCRIPT}")
        self.assertTrue(BIU_DIR.exists(), f"Missing BIU test dir: {BIU_DIR}")
        self.assertTrue(BIU_CONFIG.exists(), f"Missing BIU config: {BIU_CONFIG}")

    def assert_run_ok_and_totals(self, args):
        code, out = run_and_capture(args)
        self.assertEqual(code, 0, f"Non-zero exit ({code}) for {args}:\n{out}")
        self.assertIn("Finished executing.", out)
        total_syn, total_neu = extract_totals(out)
        self.assertIsNotNone(total_syn, f"Missing synaptic energy in output:\n{out}")
        self.assertIsNotNone(total_neu, f"Missing neurons energy in output:\n{out}")
        self.assertRegex(total_syn, r"[0-9.eE+-]+\s*fJ")
        self.assertRegex(total_neu, r"[0-9.eE+-]+\s*fJ")

    def test_default_run(self):
        self.assert_run_ok_and_totals([str(SCRIPT)])

    def test_directory_arg(self):
        self.assert_run_ok_and_totals([str(SCRIPT), str(BIU_DIR)])

    def test_explicit_config(self):
        self.assert_run_ok_and_totals([str(SCRIPT), str(BIU_CONFIG)])

    def test_multilayer_scenario(self):
        self.assertTrue(MULTI_CONFIG.exists(), f"Missing multi-layer config: {MULTI_CONFIG}")
        if MULTI_OUTPUT.exists():
            for p in MULTI_OUTPUT.glob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.assert_run_ok_and_totals([str(SCRIPT), str(MULTI_CONFIG)])
        self.assertTrue(MULTI_OUTPUT.exists(), f"Expected output dir not created: {MULTI_OUTPUT}")

    def test_per_neuron_precedence_scenario(self):
        self.assertTrue(PRECEDENCE_CONFIG.exists(), f"Missing precedence config: {PRECEDENCE_CONFIG}")
        if PRECEDENCE_OUTPUT.exists():
            for p in PRECEDENCE_OUTPUT.glob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.assert_run_ok_and_totals([str(SCRIPT), str(PRECEDENCE_CONFIG)])
        self.assertTrue(PRECEDENCE_OUTPUT.exists(), f"Expected output dir not created: {PRECEDENCE_OUTPUT}")

    def test_root_multilayer_scenario(self):
        self.assertTrue(ROOT_MULTI_CONFIG.exists(), f"Missing root multi-layer config: {ROOT_MULTI_CONFIG}")
        if ROOT_MULTI_OUTPUT.exists():
            for p in ROOT_MULTI_OUTPUT.glob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.assert_run_ok_and_totals([str(SCRIPT), str(ROOT_MULTI_CONFIG)])
        self.assertTrue(ROOT_MULTI_OUTPUT.exists(), f"Expected output dir not created: {ROOT_MULTI_OUTPUT}")

    def test_root_per_neuron_precedence_scenario(self):
        self.assertTrue(ROOT_PRECEDENCE_CONFIG.exists(), f"Missing root precedence config: {ROOT_PRECEDENCE_CONFIG}")
        if ROOT_PRECEDENCE_OUTPUT.exists():
            for p in ROOT_PRECEDENCE_OUTPUT.glob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.assert_run_ok_and_totals([str(SCRIPT), str(ROOT_PRECEDENCE_CONFIG)])
        self.assertTrue(ROOT_PRECEDENCE_OUTPUT.exists(), f"Expected output dir not created: {ROOT_PRECEDENCE_OUTPUT}")

    def test_root_multilayer_overrides_scenario(self):
        self.assertTrue(ROOT_ML_OVERRIDES_CONFIG.exists(), f"Missing root multi-layer overrides config: {ROOT_ML_OVERRIDES_CONFIG}")
        if ROOT_ML_OVERRIDES_OUTPUT.exists():
            for p in ROOT_ML_OVERRIDES_OUTPUT.glob("*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        self.assert_run_ok_and_totals([str(SCRIPT), str(ROOT_ML_OVERRIDES_CONFIG)])
        self.assertTrue(ROOT_ML_OVERRIDES_OUTPUT.exists(), f"Expected output dir not created: {ROOT_ML_OVERRIDES_OUTPUT}")


if __name__ == "__main__":
    unittest.main(verbosity=2)


