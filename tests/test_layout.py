"""Distribution layout must work regardless of checkout directory name."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootLayoutTests(unittest.TestCase):
    def test_plugin_is_self_contained_at_repository_root(self):
        for name in ("plugin.yaml", "__init__.py", "provider.py", "LICENSE", "README.md"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file(), f"Missing root distribution file: {name}")
        self.assertFalse((ROOT / "kagi").exists(), "Nested plugin would duplicate discovery")
