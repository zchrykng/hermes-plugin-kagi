"""Real Hermes directory discovery/loading; run with Hermes' Python >=3.10.

No plugin is installed: the loader reads the checkout in place. All Hermes
state is scoped to a disposable scratch home and network connects are denied.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(os.environ.get("HERMES_SOURCE", "/Users/zach/.hermes/hermes-agent"))))


@unittest.skipIf(sys.version_info < (3, 10), "Real Hermes loader requires Python >=3.10; use Hermes runtime")
class LoaderTests(unittest.TestCase):
    def test_real_profile_scope_does_not_borrow_launch_key(self):
        from kagi.provider import KagiWebSearchProvider
        from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                        set_multiplex_context, reset_multiplex_context)
        with patch.dict(os.environ, {"KAGI_API_KEY": "launch-profile-secret"}), patch(
            "urllib.request.build_opener"
        ) as build:
            token = set_secret_scope({})
            multiplex_token = set_multiplex_context(True)
            try:
                provider = KagiWebSearchProvider()
                self.assertFalse(provider.is_available())
                result = provider.search("hello")
                self.assertFalse(result["success"])
                self.assertNotIn("launch-profile-secret", result["error"])
                build.assert_not_called()
            finally:
                reset_secret_scope(token)
                reset_multiplex_context(multiplex_token)

    def test_real_discovery_registers_namespaced_provider_and_unloads(self):
        scratch = os.environ.get("TMPDIR", str(Path.home() / ".hermes/cache/scratch"))
        with tempfile.TemporaryDirectory(prefix="kagi-loader-", dir=scratch) as home, patch.dict(
            os.environ, {"HERMES_HOME": home, "HERMES_SAFE_MODE": "0"}
        ), patch("socket.socket.connect", side_effect=AssertionError("Network forbidden in tests")):
            from hermes_constants import set_hermes_home_override, reset_hermes_home_override
            token = set_hermes_home_override(home)
            try:
                from hermes_cli.plugins import PluginManager
                from hermes_cli.plugins_discovery import scan_directory
                from agent.web_search_provider import WebSearchProvider
                from agent.web_search_registry import get_provider
                manifests = scan_directory(ROOT, "user", prefix="web")
                self.assertEqual(len(manifests), 1)
                manifest = manifests[0]
                self.assertEqual(manifest.key, "web/kagi")
                manager = PluginManager(scope_key=home)
                try:
                    manager._load_plugin(manifest)
                    loaded = manager._plugins["web/kagi"]
                    self.assertIsNone(loaded.error)
                    self.assertTrue(loaded.enabled)
                    provider = get_provider("kagi", scope=home)
                    self.assertIsInstance(provider, WebSearchProvider)
                    self.assertIn("hermes_plugins.web__kagi", type(provider).__module__)
                    self.assertFalse(provider.supports_extract())
                finally:
                    manager.unload()
                self.assertIsNone(get_provider("kagi", scope=home))
            finally:
                reset_hermes_home_override(token)


if __name__ == "__main__":
    unittest.main()
