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

Use Python 3.14 and a real Hermes source checkout. CI pins upstream to
[`d923a5eb487a17c0a68801bba9ef0f56c81040a8`](https://github.com/NousResearch/hermes-agent/commit/d923a5eb487a17c0a68801bba9ef0f56c81040a8).
Keep that checkout **outside this repository** so recursive plugin discovery sees only Kagi.
`HERMES_SOURCE` selects the checkout; the default is `$HOME/.hermes/hermes-agent`.
Do not modify your installed Hermes environment to run these tests.

From this repository, using an existing checkout at that commit:

```sh
SCRATCH="${TMPDIR:-$HOME/.hermes/cache/scratch}"
mkdir -p "$SCRATCH"
TEST_ROOT=$(mktemp -d "$SCRATCH/kagi-test.XXXXXX")
mkdir -p "$TEST_ROOT/home" "$TEST_ROOT/tmp"
unset PYTHONPATH PYTHONHOME  # avoid borrowing an installed runtime's dependencies
python3.14 -m venv "$TEST_ROOT/venv"
"$TEST_ROOT/venv/bin/python" -m pip install -r requirements-ci.txt
export HERMES_HOME="$TEST_ROOT/home" TMPDIR="$TEST_ROOT/tmp"
export HERMES_SOURCE=/path/to/hermes-agent
"$TEST_ROOT/venv/bin/python" -m compileall -q kagi tests scripts
git diff --check
"$TEST_ROOT/venv/bin/python" scripts/run_tests.py
```

The isolated home must be empty initially. Only a pinned YAML parser is needed for
these real Hermes loader/config imports; the full production extras are not installed.
Tests cover the HTTP boundary, argument validation, errors, redirects, profile secrets,
and actual Hermes plugin discovery/registration/unload. HTTP responses are controlled
fixtures, not actual Kagi output. The runner fails on test errors, failures, **any skip**,
or zero discovered tests. Its own subprocess regression tests cover those conditions.

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the same checks on Ubuntu
with Python 3.14 for pushes to `main` and `master`, pull requests targeting any branch,
and manual dispatch. The single stable check name is **`CI`**; syntax, whitespace,
dependency setup, and every offline test must succeed for it to pass. Require `CI` in
the GitHub rulesets protecting `main`/`master` to make it a merge gate; the workflow
alone does not configure branch protection.

Actions and the real upstream Hermes checkout are pinned to immutable commits.
The workflow uses a read-only repository token with checkout credential persistence
disabled, no secrets, no paid API calls, and no `pull_request_target` trigger.
Hermes state and temporary files live under `RUNNER_TEMP`. Local verification is
separate from a hosted Actions run; this documentation does not assert hosted success.

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
