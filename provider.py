"""Search-only Kagi backend for Hermes."""
from __future__ import annotations

from http.client import HTTPException
import json
import urllib.request

from agent.secret_scope import get_secret
from agent.web_search_provider import WebSearchProvider


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward a paid request or its Authorization header to another URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class KagiWebSearchProvider(WebSearchProvider):
    name = "kagi"
    display_name = "Kagi"

    def get_setup_schema(self) -> dict:
        return {"name": self.display_name, "badge": "", "tag": "Paid search API",
                "env_vars": [{"key": "KAGI_API_KEY", "prompt": "Kagi API key",
                              "url": "https://kagi.com/api/keys"}]}

    def search(self, query: str, limit: int = 5) -> dict:
        if not isinstance(query, str) or not query.strip():
            return {"success": False, "error": "Kagi query must be a non-empty string."}
        if type(limit) is not int or not 1 <= limit <= 1024:
            return {"success": False, "error": "Kagi limit must be an integer from 1 to 1024."}
        try:
            key = (get_secret("KAGI_API_KEY") or "").strip()
        except Exception:
            return {"success": False, "error": "Kagi credentials unavailable in this profile."}
        if not key:
            return {"success": False, "error": "KAGI_API_KEY is not configured."}
        request = urllib.request.Request(
            "https://kagi.com/api/v1/search",
            data=json.dumps({"query": query, "workflow": "search", "format": "json",
                             "limit": limit, "safe_search": True}).encode("utf-8"),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.build_opener(_NoRedirect()).open(request, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            exc.close()
            return {"success": False, "error": f"Kagi HTTP {exc.code}; request not retried."}
        except TimeoutError:
            return {"success": False, "error": "Kagi request timed out; request not retried."}
        except (ValueError, UnicodeError):
            return {"success": False, "error": "Kagi returned invalid JSON."}
        except (OSError, HTTPException):
            return {"success": False, "error": "Kagi network failure; request not retried."}
        malformed = {"success": False, "error": "Kagi returned a malformed search response."}
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            return malformed
        meta = payload.get("meta")
        if (payload.get("error") or payload.get("errors")
                or (isinstance(meta, dict) and meta.get("status") == "error")):
            return {"success": False, "error": "Kagi API reported an error; request not retried."}
        rows = payload["data"].get("search")
        if not isinstance(rows, list):
            return malformed
        web = []
        for index, row in enumerate(rows[:limit], 1):
            if (not isinstance(row, dict) or not isinstance(row.get("url"), str)
                    or not isinstance(row.get("title"), str)
                    or (row.get("snippet") is not None and not isinstance(row["snippet"], str))):
                return malformed
            web.append({"url": row["url"], "title": row["title"],
                        "description": row.get("snippet") or "", "position": index})
        return {"success": True, "data": {"web": web}}

    def is_available(self) -> bool:
        try:
            return bool((get_secret("KAGI_API_KEY") or "").strip())
        except Exception:
            return False
