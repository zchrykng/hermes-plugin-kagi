"""Real Hermes directory discovery/loading; run with Hermes' Python >=3.10.

No active plugin is installed: the loader reads an isolated installed-layout copy.
All Hermes state is scoped to a disposable scratch home; network connects are denied.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(os.environ.get("HERMES_SOURCE", str(Path.home() / ".hermes" / "hermes-agent")))))


@unittest.skipIf(sys.version_info < (3, 10), "Real Hermes loader requires Python >=3.10; use Hermes runtime")
class LoaderTests(unittest.TestCase):
    def setUp(self):
        network = patch("socket.socket.connect", side_effect=AssertionError("Network forbidden in profile tests"))
        network.start()
        self.addCleanup(network.stop)

    def test_served_key_wins_over_launch_environment(self):
        import io
        from plugin_under_test import KagiWebSearchProvider
        from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                        set_multiplex_context, reset_multiplex_context)
        with patch.dict(os.environ, {"KAGI_API_KEY": "synthetic-launch-key"}), patch(
            "urllib.request.build_opener"
        ) as build:
            build.return_value.open.return_value = io.BytesIO(b'{"data":{"search":[]}}')
            scope = set_secret_scope({"KAGI_API_KEY": "  synthetic-served-key  "})
            multiplex = set_multiplex_context(True)
            try:
                provider = KagiWebSearchProvider()
                self.assertTrue(provider.is_available())
                self.assertTrue(provider.search("hello")["success"])
                request = build.return_value.open.call_args.args[0]
                self.assertEqual(request.get_header("Authorization"), "Bearer synthetic-served-key")
            finally:
                reset_secret_scope(scope)
                reset_multiplex_context(multiplex)

    def test_multiplex_without_scope_fails_before_http(self):
        from plugin_under_test import KagiWebSearchProvider
        from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                        set_multiplex_context, reset_multiplex_context)
        with patch.dict(os.environ, {"KAGI_API_KEY": "synthetic-launch-key"}), patch(
            "urllib.request.build_opener"
        ) as build:
            scope = set_secret_scope(None)
            multiplex = set_multiplex_context(True)
            try:
                provider = KagiWebSearchProvider()
                self.assertFalse(provider.is_available())
                self.assertEqual(provider.search("hello"), {
                    "success": False, "error": "Kagi credentials unavailable in this profile."
                })
                build.assert_not_called()
            finally:
                reset_secret_scope(scope)
                reset_multiplex_context(multiplex)

    def test_concurrent_scopes_keep_authorization_separate(self):
        import io
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from unittest.mock import MagicMock
        from plugin_under_test import KagiWebSearchProvider
        from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                        set_multiplex_context, reset_multiplex_context)
        barrier = Barrier(2)
        provider = KagiWebSearchProvider()
        def serve(key):
            scope = set_secret_scope({"KAGI_API_KEY": key})
            multiplex = set_multiplex_context(True)
            try:
                barrier.wait(timeout=5)
                return provider.is_available(), provider.search(key)
            finally:
                reset_secret_scope(scope)
                reset_multiplex_context(multiplex)
        def open_request(request, **kwargs):
            self.assertEqual(request.get_header("Authorization"), "Bearer " + json.loads(request.data)["query"])
            return io.BytesIO(b'{"data":{"search":[]}}')
        opener = MagicMock()
        opener.open.side_effect = open_request
        with patch("urllib.request.build_opener", return_value=opener), ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(serve, key) for key in ("synthetic-a", "synthetic-b")]
            for future in futures:
                available, result = future.result(timeout=10)
                self.assertTrue(available)
                self.assertTrue(result["success"])
        self.assertEqual(opener.open.call_count, 2)

    def test_real_profile_scope_does_not_borrow_launch_key(self):
        from plugin_under_test import KagiWebSearchProvider
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

    def test_empty_served_scope_never_reads_launch_dotenv(self):
        from plugin_under_test import KagiWebSearchProvider
        from agent.secret_scope import (set_secret_scope, reset_secret_scope,
                                        set_multiplex_context, reset_multiplex_context)
        from hermes_constants import set_hermes_home_override, reset_hermes_home_override
        scratch = os.environ.get("TMPDIR", str(Path.home() / ".hermes/cache/scratch"))
        with tempfile.TemporaryDirectory(prefix="kagi-launch-", dir=scratch) as home:
            (Path(home) / ".env").write_text("KAGI_API_KEY=synthetic-launch-dotenv-key\n")
            with patch.dict(os.environ, {"HERMES_HOME": home}), patch(
                "socket.socket.connect", side_effect=AssertionError("Network forbidden")
            ), patch("urllib.request.build_opener") as build:
                import io
                build.return_value.open.return_value = io.BytesIO(b'{"data":{"search":[]}}')
                os.environ.pop("KAGI_API_KEY", None)
                home_token = set_hermes_home_override(home)
                scope_token = set_secret_scope({})
                multiplex_token = set_multiplex_context(True)
                # Even opening the launch .env after scope binding is forbidden.
                from builtins import open as real_open
                reads = []
                def guarded_open(file, *args, **kwargs):
                    if Path(file) == Path(home) / ".env":
                        reads.append(str(file))
                    return real_open(file, *args, **kwargs)
                try:
                    with patch("builtins.open", side_effect=guarded_open):
                        provider = KagiWebSearchProvider()
                        available = provider.is_available()
                        result = provider.search("hello")
                    self.assertEqual(reads, [])
                    self.assertFalse(available)
                    self.assertFalse(result["success"])
                    self.assertNotIn("synthetic-launch-dotenv-key", str(result))
                    build.assert_not_called()
                finally:
                    reset_multiplex_context(multiplex_token)
                    reset_secret_scope(scope_token)
                    reset_hermes_home_override(home_token)

    def test_real_parser_preserves_install_metadata(self):
        from hermes_cli.plugins_manifest import parse_manifest_file
        manifest = parse_manifest_file(ROOT / "plugin.yaml", ROOT, "user", "")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest.key, "kagi")
        self.assertEqual(manifest.name, "kagi")
        self.assertEqual(manifest.requires_env, [{
            "name": "KAGI_API_KEY", "description": "Kagi API key with paid search access",
            "secret": True, "url": "https://kagi.com/api/keys"
        }])
        self.assertEqual(manifest.requires_hermes, ">=0.22.2")
        self.assertEqual(manifest.author, "Zachary King")
        self.assertEqual(manifest.homepage, "https://github.com/zchrykng/hermes-plugin-kagi")
        self.assertEqual(manifest.license, "MIT")
        self.assertEqual(manifest.tags, ["web", "kagi", "search"])
        self.assertEqual(manifest.version, "0.1.0")
        self.assertEqual(manifest.kind, "backend")

    def test_real_discovery_registers_root_provider_and_unloads(self):
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
                # Rehearse the installed layout without scanning sibling projects.
                import shutil
                plugins = Path(home) / "plugins"
                installed = plugins / "kagi"
                installed.mkdir(parents=True)
                for name in ("plugin.yaml", "__init__.py", "provider.py", "LICENSE", "README.md"):
                    shutil.copy2(ROOT / name, installed / name)
                manifests = scan_directory(plugins, "user")
                self.assertEqual(len(manifests), 1)
                manifest = manifests[0]
                self.assertEqual(manifest.key, "kagi")
                from agent.secret_scope import set_secret_scope, reset_secret_scope
                secret_token = set_secret_scope({"KAGI_API_KEY": "synthetic-loader-key"})
                manager = PluginManager(scope_key=home)
                try:
                    manager._load_plugin(manifest)
                    loaded = manager._plugins["kagi"]
                    self.assertIsNone(loaded.error)
                    self.assertTrue(loaded.enabled)
                    provider = get_provider("kagi", scope=home)
                    self.assertIsInstance(provider, WebSearchProvider)
                    self.assertIn("hermes_plugins.kagi", type(provider).__module__)
                    self.assertFalse(provider.supports_extract())
                finally:
                    manager.unload()
                    reset_secret_scope(secret_token)
                self.assertIsNone(get_provider("kagi", scope=home))
            finally:
                reset_hermes_home_override(token)


if __name__ == "__main__":
    unittest.main()
