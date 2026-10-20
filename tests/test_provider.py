"""Offline contract tests against the installed Hermes ABC (no Kagi calls)."""
import importlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERMES_SOURCE = Path(os.environ.get("HERMES_SOURCE", "/Users/zach/.hermes/hermes-agent"))
sys.path.insert(0, str(HERMES_SOURCE))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.web_search_provider import WebSearchProvider

try:
    from kagi.provider import KagiWebSearchProvider
except ModuleNotFoundError:
    KagiWebSearchProvider = None


class ProviderTests(unittest.TestCase):
    def test_availability_uses_profile_safe_lookup_without_http(self):
        with patch("kagi.provider.get_provider_env", return_value="test-key") as lookup:
            self.assertTrue(KagiWebSearchProvider().is_available())
            lookup.assert_called_once_with("KAGI_API_KEY")
        with patch("kagi.provider.get_provider_env", return_value=""):
            self.assertFalse(KagiWebSearchProvider().is_available())
        with patch("kagi.provider.get_provider_env", side_effect=RuntimeError("scope denied")):
            self.assertFalse(KagiWebSearchProvider().is_available())

    def test_search_posts_bearer_json_and_normalizes_results(self):
        from unittest.mock import MagicMock
        response = io.BytesIO(json.dumps({"meta": {}, "data": {"search": [
            {"url": "https://example.com", "title": "Example", "snippet": "A snippet"}
        ]}}).encode())
        opener = MagicMock()
        opener.open.return_value = response
        with patch("kagi.provider.get_provider_env", return_value="test-key"), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            result = KagiWebSearchProvider().search("a query", limit=1)
        self.assertEqual(result, {"success": True, "data": {"web": [
            {"url": "https://example.com", "title": "Example", "description": "A snippet", "position": 1}
        ]}})
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://kagi.com/api/v1/search")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), {"query": "a query", "workflow": "search",
                                                  "format": "json", "limit": 1, "safe_search": True})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)

    def test_invalid_input_is_rejected_before_credentials_or_http(self):
        for query, limit in [("", 5), ("  ", 5), (None, 5), (123, 5), ("ok", 0),
                             ("ok", 1025), ("ok", True), ("ok", 1.5), ("ok", "5")]:
            with self.subTest(query=query, limit=limit), patch("kagi.provider.get_provider_env") as lookup, patch("urllib.request.build_opener") as build:
                result = KagiWebSearchProvider().search(query, limit)
                self.assertFalse(result["success"])
                self.assertIsInstance(result["error"], str)
                lookup.assert_not_called()
                build.assert_not_called()

    def test_missing_or_inaccessible_credentials_never_send_http(self):
        for options in [{"return_value": ""}, {"side_effect": RuntimeError("secret-key")}]:
            with self.subTest(options=options), patch("kagi.provider.get_provider_env", **options), patch("urllib.request.build_opener") as build:
                result = KagiWebSearchProvider().search("hello")
                self.assertFalse(result["success"])
                self.assertNotIn("secret-key", result["error"])
                build.assert_not_called()

    def test_http_failures_are_sanitized_and_never_retried(self):
        from urllib.error import HTTPError, URLError
        from unittest.mock import MagicMock
        cases = [(HTTPError("https://kagi.com", code, "secret-key", {}, io.BytesIO(b"secret-key")), str(code))
                 for code in (301, 302, 307, 308, 400, 401, 403, 429, 500, 503)]
        cases += [(TimeoutError("secret-key"), "timed out"),
                  (URLError("secret-key"), "network"), (OSError("secret-key"), "network")]
        for error, expected in cases:
            with self.subTest(error=error):
                opener = MagicMock()
                opener.open.side_effect = error
                with patch("kagi.provider.get_provider_env", return_value="secret-key"), patch("urllib.request.build_opener", return_value=opener):
                    result = KagiWebSearchProvider().search("hello")
                self.assertFalse(result["success"])
                self.assertIn(expected, result["error"])
                self.assertNotIn("secret-key", result["error"])
                opener.open.assert_called_once()

    def test_incomplete_response_is_sanitized_and_never_retried(self):
        from http.client import IncompleteRead
        from unittest.mock import MagicMock

        class IncompleteResponse(io.BytesIO):
            reads = 0

            def read(self, *args, **kwargs):
                self.reads += 1
                raise IncompleteRead(b'{"secret-key": "private-response-body"}', 100)

        response = IncompleteResponse()
        opener = MagicMock()
        opener.open.return_value = response
        with patch("kagi.provider.get_provider_env", return_value="secret-key"), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            result = KagiWebSearchProvider().search("hello")
        self.assertEqual(result, {
            "success": False, "error": "Kagi network failure; request not retried."
        })
        self.assertNotIn("secret-key", json.dumps(result))
        self.assertNotIn("private-response-body", json.dumps(result))
        opener.open.assert_called_once()
        self.assertEqual(response.reads, 1)
        self.assertTrue(response.closed)

    def test_redirect_never_forwards_bearer_token(self):
        import urllib.request
        from urllib.response import addinfourl
        from email.message import Message

        class RedirectTransport(urllib.request.HTTPSHandler):
            calls = []

            def https_open(self, request):
                self.calls.append(request)
                headers = Message()
                headers["Location"] = "https://attacker.invalid/collect"
                response = addinfourl(io.BytesIO(b""), headers, request.full_url, 302)
                response.msg = "Found"
                return response

        transport = RedirectTransport()
        real_builder = urllib.request.build_opener
        with patch("kagi.provider.get_provider_env", return_value="secret-key"), patch(
            "urllib.request.build_opener", side_effect=lambda *handlers: real_builder(transport, *handlers)
        ):
            result = KagiWebSearchProvider().search("hello")
        self.assertFalse(result["success"])
        self.assertIn("302", result["error"])
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0].full_url, "https://kagi.com/api/v1/search")

    def test_optional_snippet_empty_results_and_limit_bound(self):
        from unittest.mock import MagicMock
        for rows, limit, expected in [([], 1024, []), ([{"url": "https://a", "title": "A"},
                {"url": "https://b", "title": "B", "snippet": None}], 1,
                [{"url": "https://a", "title": "A", "description": "", "position": 1}])]:
            with self.subTest(rows=rows):
                opener = MagicMock()
                opener.open.return_value = io.BytesIO(json.dumps({"data": {"search": rows}}).encode())
                with patch("kagi.provider.get_provider_env", return_value="test-key"), patch("urllib.request.build_opener", return_value=opener):
                    self.assertEqual(KagiWebSearchProvider().search("hello", limit),
                                     {"success": True, "data": {"web": expected}})

    def test_malformed_responses_fail_without_echoing_body(self):
        from unittest.mock import MagicMock
        bodies = [b"<html>secret-key</html>", b"\xff", b"null", b"[]", b"{}",
                  json.dumps({"data": None}).encode(), json.dumps({"data": {"search": {}}}).encode(),
                  json.dumps({"data": {"search": [None]}}).encode(),
                  json.dumps({"data": {"search": [{"url": "https://a"}]}}).encode(),
                  json.dumps({"data": {"search": [{"url": 123, "title": "a"}]}}).encode(),
                  json.dumps({"data": {"search": [{"url": "https://a", "title": [], "snippet": "secret-key"}]}}).encode(),
                  json.dumps({"data": {"search": [{"url": "https://a", "title": "a", "snippet": {}}]}}).encode()]
        for body in bodies:
            with self.subTest(body=body):
                opener = MagicMock()
                opener.open.return_value = io.BytesIO(body)
                with patch("kagi.provider.get_provider_env", return_value="secret-key"), patch("urllib.request.build_opener", return_value=opener):
                    result = KagiWebSearchProvider().search("hello")
                self.assertFalse(result["success"])
                self.assertIsInstance(result["error"], str)
                self.assertNotIn("secret-key", result["error"])

    def test_in_body_errors_are_not_mistaken_for_empty_success(self):
        from unittest.mock import MagicMock
        for envelope in [{"error": "secret-key"}, {"errors": [{"message": "secret-key"}]},
                         {"meta": {"status": "error", "message": "secret-key"}}]:
            with self.subTest(envelope=envelope):
                opener = MagicMock()
                opener.open.return_value = io.BytesIO(json.dumps(dict(envelope, data={"search": []})).encode())
                with patch("kagi.provider.get_provider_env", return_value="secret-key"), patch("urllib.request.build_opener", return_value=opener):
                    result = KagiWebSearchProvider().search("hello")
                self.assertFalse(result["success"])
                self.assertNotIn("secret-key", result["error"])

    def test_package_registers_search_provider_and_declares_manifest(self):
        from unittest.mock import MagicMock
        package = importlib.import_module("kagi")
        self.assertTrue(callable(getattr(package, "register", None)), "register(ctx) missing")
        ctx = MagicMock()
        package.register(ctx)
        ctx.register_web_search_provider.assert_called_once()
        self.assertIsInstance(ctx.register_web_search_provider.call_args.args[0], WebSearchProvider)
        manifest = (Path(__file__).resolve().parents[1] / "kagi" / "plugin.yaml").read_text()
        self.assertEqual(manifest.splitlines()[0], "name: kagi")
        self.assertIn("kind: backend", manifest)
        self.assertIn("provides_web_providers:", manifest)
        self.assertIn("  - kagi", manifest)

    def test_setup_schema_identifies_paid_key(self):
        provider = KagiWebSearchProvider()
        self.assertEqual(provider.display_name, "Kagi")
        schema = provider.get_setup_schema()
        self.assertEqual(schema["name"], "Kagi")
        self.assertEqual(schema["env_vars"][0]["key"], "KAGI_API_KEY")
        self.assertIn("paid", schema["tag"].lower())

    def test_real_hermes_search_only_identity(self):
        self.assertIsNotNone(KagiWebSearchProvider, "Kagi provider is not implemented")
        provider = KagiWebSearchProvider()
        self.assertIsInstance(provider, WebSearchProvider)
        self.assertEqual(provider.name, "kagi")
        self.assertTrue(provider.supports_search())
        self.assertFalse(provider.supports_extract())
        self.assertFalse(provider.is_keyless_available())


if __name__ == "__main__":
    unittest.main()
