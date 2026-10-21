"""Hermes directory-plugin entry point; supports namespaced loading."""
from .provider import KagiWebSearchProvider


def register(ctx):
    ctx.register_web_search_provider(KagiWebSearchProvider())
