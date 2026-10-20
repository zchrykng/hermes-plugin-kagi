"""Run unittest discovery, rejecting empty suites (including in CI)."""
from pathlib import Path
import sys
import unittest


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[1] / "tests")
    suite = unittest.defaultTestLoader.discover(directory)
    if suite.countTestCases() == 0:
        print("No tests discovered", file=sys.stderr)
        return 1
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print("Skipped tests are forbidden", file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
