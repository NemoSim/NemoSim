import os
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "run_nemosim.sh"
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

# Expected pinned totals per scenario
EXPECTED = {
    "default": ("1.45099e+06 fJ", "3.86833e+08 fJ"),
    "biu_dir": ("1.45099e+06 fJ", "3.86833e+08 fJ"),
    "biu_config": ("1.45099e+06 fJ", "3.86833e+08 fJ"),
    "root_multi": ("3.58167e+07 fJ", "4.00494e+08 fJ"),
    "root_precedence": ("4.74923e+06 fJ", "3.8236e+09 fJ"),
    "root_ml_overrides": ("1.28865e+07 fJ", "6.57939e+09 fJ"),
    # Optional: BIU-dir variants (should match root equivalents if inputs same)
    "biu_multi": ("3.58167e+07 fJ", "4.00494e+08 fJ"),
    "biu_precedence": ("4.74923e+06 fJ", "3.8236e+09 fJ"),
}


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


def assert_output_sanity(testcase: unittest.TestCase, output_dir: Path):
    # Basic sanity: at least one of each expected file type exists and is non-empty
    spikes = sorted(output_dir.glob("spikes_*.txt"))
    vin = sorted(output_dir.glob("vin_*.txt"))
    vns = sorted(output_dir.glob("vns_*.txt"))
    testcase.assertGreaterEqual(len(spikes), 1, f"No spikes_*.txt in {output_dir}")
    testcase.assertGreaterEqual(len(vin), 1, f"No vin_*.txt in {output_dir}")
    testcase.assertGreaterEqual(len(vns), 1, f"No vns_*.txt in {output_dir}")
    # Non-empty and minimum line counts (>= 10 lines) as a rough sanity
    for f in [spikes[0], vin[0], vns[0]]:
        size = f.stat().st_size
        testcase.assertGreater(size, 0, f"Empty output file: {f}")
        with f.open("r") as fh:
            cnt = sum(1 for _ in fh)
        testcase.assertGreaterEqual(cnt, 10, f"Too few lines in {f}: {cnt}")


class TestNemoSimRunner(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), f"Missing script: {SCRIPT}")
        self.assertTrue(os.access(SCRIPT, os.X_OK), f"Script not executable: {SCRIPT}")
        self.assertTrue(BIU_DIR.exists(), f"Missing BIU test dir: {BIU_DIR}")
        self.assertTrue(BIU_CONFIG.exists(), f"Missing BIU config: {BIU_CONFIG}")

    def assert_run_ok_totals_pinned(self, args, expected_key: str, output_dir: Path | None = None):
        code, out = run_and_capture(args)
        self.assertEqual(code, 0, f"Non-zero exit ({code}) for {args}:\n{out}")
        self.assertIn("Finished executing.", out)
        total_syn, total_neu = extract_totals(out)
        self.assertIsNotNone(total_syn, f"Missing synaptic energy in output:\n{out}")
        self.assertIsNotNone(total_neu, f"Missing neurons energy in output:\n{out}")
        exp_syn, exp_neu = EXPECTED[expected_key]
        self.assertEqual(total_syn, exp_syn, f"Synaptic energy mismatch for {expected_key}")
        self.assertEqual(total_neu, exp_neu, f"Neurons energy mismatch for {expected_key}")
        if output_dir is not None:
            self.assertTrue(output_dir.exists(), f"Expected output dir not created: {output_dir}")
            assert_output_sanity(self, output_dir)

    def test_default_run(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT)], "default", BIU_DIR / "output_directory")

    def test_directory_arg(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(BIU_DIR)], "biu_dir", BIU_DIR / "output_directory")

    def test_explicit_config(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(BIU_CONFIG)], "biu_config", BIU_DIR / "output_directory")

    def test_multilayer_scenario(self):
        # BIU-dir variant
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(MULTI_CONFIG)], "biu_multi", MULTI_OUTPUT)

    def test_per_neuron_precedence_scenario(self):
        # BIU-dir variant
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(PRECEDENCE_CONFIG)], "biu_precedence", PRECEDENCE_OUTPUT)

    def test_root_multilayer_scenario(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(ROOT_MULTI_CONFIG)], "root_multi", ROOT_MULTI_OUTPUT)

    def test_root_per_neuron_precedence_scenario(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(ROOT_PRECEDENCE_CONFIG)], "root_precedence", ROOT_PRECEDENCE_OUTPUT)

    def test_root_multilayer_overrides_scenario(self):
        self.assert_run_ok_totals_pinned([str(SCRIPT), str(ROOT_ML_OVERRIDES_CONFIG)], "root_ml_overrides", ROOT_ML_OVERRIDES_OUTPUT)


if __name__ == "__main__":
    unittest.main(verbosity=2)


