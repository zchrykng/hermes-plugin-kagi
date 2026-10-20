# Kagi for Hermes Agent

A Hermes plugin for Kagi's useful API capabilities. Plugin name and provider ID: `kagi`.

**Implemented:** native web search through Kagi's v1 API. **Planned:** extraction, specialized search, enrichment, summarization, FastGPT, and Small Web discovery. See [PROJECT.md](PROJECT.md) for the roadmap.

This is an independent integration, not an official Kagi or Nous Research plugin.

## Features

- Powers Hermes's standard `web_search` tool.
- Profile-aware `KAGI_API_KEY` lookup through Hermes's credential helper.
- Input validation, a 30-second request timeout, sanitized errors, and redirect blocking.
- No automatic retries, pagination, extraction, or provider fallback inside the plugin.
- Safe search explicitly enabled in this initial version.

Kagi API access/billing must be configured separately; do not assume a regular search subscription includes API usage. Check [API pricing](https://kagi.com/api/pricing).

## Requirements

- A Hermes installation providing `WebSearchProvider`, `get_provider_env`, and namespaced user backend discovery.
- A Kagi API key with search access and available API credit.
- The provider uses Python's standard library; no additional HTTP SDK is required.

Hermes's plugin interfaces evolve. Offline tests exercise the real installed provider interface and loader rather than substituting a fake Hermes interface. A broader version compatibility matrix is not established yet.

## Install

Clone this repository and enter it:

```sh
git clone https://github.com/zchrykng/hermes-plugin-kagi.git
cd hermes-plugin-kagi
```

Install into the intended profile's Hermes home. Do not overwrite an existing installation without reviewing its contents:

```sh
PLUGIN_HOME="${HERMES_HOME:-$HOME/.hermes}/plugins/web"
if [ -e "$PLUGIN_HOME/kagi" ]; then
  printf 'Kagi plugin already exists; review it before updating.\n'
else
  mkdir -p "$PLUGIN_HOME"
  cp -R kagi "$PLUGIN_HOME/kagi"
fi
hermes plugins enable web/kagi
```

The loader identity is `web/kagi`; the plugin manifest name and provider ID are `kagi`. The loader identity is a stable installation namespace, not the public plugin name.

Store `KAGI_API_KEY` in the selected profile's secret storage (`.env`), not `config.yaml`, source files, shell history, or chat. Get an API key at https://kagi.com/api/keys.

Record the previous search backend for rollback, then select Kagi:

```sh
hermes config get web.search_backend
hermes config set web.search_backend kagi
hermes plugins show web/kagi
```

Leave `web.extract_backend` on your current extraction provider. Restart your Hermes gateway through its usual controls and open a new chat so it discovers the plugin.

## Test a live search

Search routing has been manually verified in a development installation. Automated tests do not make authenticated Kagi requests or verify your account's API permissions.

A live test may incur a charge. Ask Hermes:

> Use web_search once to search for “Kagi official documentation,” with a limit of 3. Do not retry or use a fallback if it fails.

Confirm the runtime log contains `Web search via kagi` for that call. Check Kagi's API dashboard for independent usage confirmation. Results alone do not establish which backend served a request. Hermes may apply wrapper-level caching/fallback behavior independently of this plugin's single-attempt policy.

To roll back, restore the prior `web.search_backend` value. If the setting was previously absent, use `hermes config unset web.search_backend`. Disable the plugin with `hermes plugins disable web/kagi` and reload the gateway.

## Run offline tests

Use a Hermes-compatible Python with the installed Hermes dependencies. Set `HERMES_SOURCE` to your Hermes source checkout. Run from this repository with a disposable `HERMES_HOME`: the credential-isolation test assumes an empty profile.

```sh
SCRATCH="${TMPDIR:-$HOME/.hermes/cache/scratch}"
mkdir -p "$SCRATCH"
TEST_HOME=$(mktemp -d "$SCRATCH/kagi-test.XXXXXX")
HERMES_HOME="$TEST_HOME" HERMES_SOURCE=/path/to/hermes-agent \
  /path/to/hermes-python -m unittest discover -s tests -v
```

Tests cover the HTTP boundary, argument validation, errors, redirects, profile secrets, and actual Hermes plugin discovery/registration/unload. HTTP responses are controlled fixtures, not actual Kagi output. Older Python runtimes may skip loader integration tests; use Hermes's own runtime for the full suite. No CI workflow is configured yet.

## Project layout

- `kagi/` — backend manifest, registration entry point, and provider.
- `tests/` — offline provider and loader tests.
- `PROJECT.md` — architecture, scope, and follow-up milestones.

## Alternative

Kagi offers an official hosted MCP server at https://mcp.kagi.com/mcp. Use that if separate Kagi tools are sufficient and you do not need to replace Hermes's standard search backend.

## References

- https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin
- https://kagi.com/api/docs
- https://kagi.com/api/docs/_bundle/openapi.json
