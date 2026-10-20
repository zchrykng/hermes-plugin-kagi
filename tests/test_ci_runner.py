"""Exercise CI's fail-closed runner with disposable unittest suites."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_tests.py"


class CIRunnerTests(unittest.TestCase):
    def run_fixture(self, source=""):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            if source:
                (Path(directory) / "test_fixture.py").write_text(source)
            return subprocess.run(
                [sys.executable, str(RUNNER), directory],
                capture_output=True, text=True, check=False,
            )

    def test_passing_suite_succeeds(self):
        result = self.run_fixture(
            "import unittest\nclass Fixture(unittest.TestCase):\n"
            "    def test_example(self): self.assertTrue(True)\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ran 1 test", result.stderr)

    def test_failing_suite_fails(self):
        result = self.run_fixture(
            "import unittest\nclass Fixture(unittest.TestCase):\n"
            "    def test_example(self): self.fail('fixture failure')\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture failure", result.stderr)

    def test_import_error_fails(self):
        result = self.run_fixture("raise RuntimeError('fixture import failure')\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture import failure", result.stderr)

    def test_skipped_test_fails(self):
        result = self.run_fixture(
            "import unittest\n"
            "class Fixture(unittest.TestCase):\n"
            "    @unittest.skip('not available')\n"
            "    def test_example(self): pass\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Skipped tests are forbidden", result.stderr)

    def test_empty_discovery_fails(self):
        result = self.run_fixture()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No tests discovered", result.stderr)
