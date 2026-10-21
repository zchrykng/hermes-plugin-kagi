# Kagi plugin development audit

> Historical audit of revision `5111a34`. Credential API, manifest metadata,
> licensing, and root packaging findings have since been addressed in the working
> candidate. This document retains the original findings; it is not a claim that
> managed installation, active-copy migration, or catalogue submission is complete.

## Scope and verdict

Audited repository revision `5111a34bec77aa7c1d5b8995ea298797f148fc9f` against the current official general plugin guide, web-provider guide, catalogue submission rules, and relevant installed Hermes source. This is a read-only implementation audit; the report itself is the only project file added. No paid Kagi requests, active-plugin migration, license change, or release submission was performed.

**Verdict:** the existing search provider follows the native provider contract and works, but the project is not yet ready to call catalogue-compliant or distribution-complete. Validator success is necessary but does not establish every human-reviewed policy requirement.

## Verified evidence

- `hermes plugins validate ./kagi --install-deps --json` previously returned `ok: true`, no warnings, and security scan `safe`.
- A fresh `hermes plugins doctor ./kagi --ci` run passed real discovery, parsing, import and registration. Zero directly registered tools/hooks is expected: this is a provider, not a replacement tool.
- GitHub Actions passed on main revision `5111a34`; its suite exercises 20 offline tests against pinned real Hermes source `d923a5eb487a17c0a68801bba9ef0f56c81040a8` (0.22.2).
- Branch ruleset 25501420 is active on main/master, requires CI and an up-to-date PR, blocks force pushes/deletion, and has no bypass actors.
- Runtime provider: fixed HTTPS Kagi v1 POST endpoint, Bearer auth, no redirects or automatic retries, socket timeout, sanitized HTTP/JSON/network errors including truncated response handling, standard dict result envelope and one-based positions.
- `is_available()` is read-only and network-free; inherited search/extract/keyless capability defaults are appropriate.
- No plugin core monkeypatch, self-updater, credential-file parser, telemetry, binary payload or unnecessary runtime SDK dependency was found.

## Findings

### 1. Credential API and declarations — resolve before catalogue submission

`kagi/provider.py:8,33,79` uses Hermes's `get_provider_env`. It is scope-aware and itself delegates into Hermes's secret/config machinery, so this audit does not establish a credential leak. Nevertheless catalogue rule 11 expressly prescribes `agent.secret_scope.get_secret` for declared plugin secrets. Adopt that surface and fail closed on invalid/missing profile scope rather than seeking an exception for this small adapter.

`kagi/plugin.yaml` does not declare `requires_env`. The provider's `get_setup_schema` is picker metadata, not a replacement for the manifest-driven install credential prompt. Add rich `KAGI_API_KEY` metadata including secret status and current key URL. Do not read `.env` or any credential store in plugin code.

Coverage needs synthetic launch `.env` versus served-profile scopes, positive served-key selection, missing served key, absent scope during multiplexing, and concurrent profile separation. Existing tests cover a launch process-environment key under an empty routed scope, not the entire matrix. The current config helper can call `load_env()` after a scoped miss; the caller's bound Hermes home matters. Do not describe that observation as proof of an active cross-profile exploit.

### 2. Managed installation identity and migration — approved deployment change

The manual copy instructions create `plugins/web/kagi` with loader key `web/kagi`. The managed Git installer reads `name: kagi` and installs into `plugins/kagi`, with loader key `kagi`; selecting source subdir `kagi` does not preserve a destination namespace. Both layouts are supported, but co-installation risks duplicate provider registration.

Use the managed loader key `kagi` for new distribution, retain provider ID and `web.search_backend: kagi`, and document the old key only as legacy. Do not put a slash in the manifest name to force the old path.

Migration acceptance gates:
1. Verify tests and catalogue checks for the candidate commit.
2. Exercise pinned managed Git/subdir installation, discovery and enablement in a disposable home with synthetic credentials only; verify source/provenance and update semantics.
3. Inspect the real active profile, backend, settings and local modifications without exposing secrets.
4. Back up the old copy outside the entire scanned plugins tree, disable its old key, and install/verify the candidate initially disabled.
5. Enable the managed `kagi` copy, reload through normal gateway controls, and confirm one provider registration and unchanged backend selection.
6. Preserve a rollback path. Do not make another paid search unless explicitly authorized.

Supported source form, using the candidate commit rather than the historical SHA below:

```sh
hermes plugins install zchrykng/hermes-plugin-kagi/kagi --ref <full-commit-SHA> --no-enable
```

Manual copies lack managed provenance and cannot automatically gain managed updates. Explicit custom Git pins move through a deliberate reinstall with `--force --ref`; catalogue updates require reviewed catalogue SHA-bump PRs.

### 3. Distributable documentation and license — release preparation

A catalogue entry with `subdir: kagi` renders the README from that subtree, and subdirectory installation excludes root-only documentation. Add `kagi/README.md` with self-contained setup, paid-service/data disclosure, actual capabilities, supported versions and update/migration instructions. Avoid broken relative links back to excluded root files.

No tracked license exists. The owner selected MIT; add the full grant at repository root and within the distributable subtree, plus `license: MIT` metadata. A license is legal/distribution readiness, not an explicitly stated catalogue rule in the reviewed admission list.

Explicitly disclose that search queries and API authentication go to Kagi, that API charges apply, and that there is no plugin-owned telemetry, key persistence or background process. State what was actually verified rather than promising every planned capability.

### 4. Compatibility and metadata — improve before release

Add author/homepage and a tested `requires_hermes` SemVer floor. Current test evidence supports 0.22.2; do not claim older releases without testing. Absent metadata is accepted by the validator, but when provided it must be truthful. Quote the plugin version for consistency with release/catalogue metadata. Tags are optional.

Keeping the v1 manifest and nested package is supported. Manifest v2, pip distribution, an extra SDK, a desktop UI, custom tools, or a global plugin API number are not required for this search backend. The general guide's JSON-string handler requirement applies to direct tool handlers; provider methods correctly return dict envelopes.

### 5. CI — functional, but does not enforce all catalogue checks

The current workflow runs syntax and unit/integration tests securely with a read-only token, pinned actions/upstream source, no stored checkout credentials, no secrets, and no `pull_request_target`. The runner rejects skipped and empty suites.

Add real plugin Doctor and catalogue validator steps to CI. Ensure validator dependency preparation is performed in an isolated environment compatible with Hermes's package-management rules. Do not assume the minimal loader-test dependency set supports the full validation command. Keep a stable required CI check.

The current `git diff --check` runs on a clean checkout and therefore does not meaningfully inspect whitespace introduced by a PR. Compare the correct base/head range or use a source-aware whitespace check with sufficient Git history.

Update pinned actions to supported Node runtimes when practical: hosted runs currently warn about forced Node 20-to-24 migration. This is maintenance, not a test failure. Consider separate advisory testing of newer Hermes while retaining a reproducible required baseline.

### 6. Resource handling — recommended hardening

`json.load(response)` is unbounded; result slicing only limits output after download and parse. Add a response byte cap, safe errors for excessive nesting/invalid encoding and well-chosen input limits. A 30-second socket timeout is not a guaranteed total wall-clock deadline. Test the boundaries and document the actual budget. These are resilience recommendations, not a provider contract rule imposing a particular size/deadline.

Add a native dispatcher integration test beyond direct provider and loader tests. Keep fixture tests distinct from the already-confirmed manual live search and from billing evidence.

## Owner decisions

Confirmed during this audit:
- License: MIT.
- First catalogue release: working search-only capability, not the full roadmap.
- Submission: manual release submission with an approval gate; upstream maintainers still review every pin.
- Distribution: adopt managed installation and migrate the active legacy copy after tests pass, with backup/rollback.

No additional product decision is required for the obvious metadata, scoped-secret, packaging, CI and resource-hardening fixes. Implementations and release actions have not occurred as part of this audit.

## Suggested execution order

1. Make scoped-secret and manifest changes with regression tests.
2. Add MIT license and distributable docs; establish tested compatibility floor.
3. Harden response handling and strengthen native-dispatch/profile tests.
4. Put Doctor and catalogue validation in CI and verify hosted success through a protected PR.
5. Test managed pinned installation in an isolated home; then perform the approved active-copy migration with rollback.
6. Prepare a versioned search-only release and catalogue entry pinned to the exact green commit. Require owner approval before publishing/submitting.

## Sources

- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin
- https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission
- https://raw.githubusercontent.com/NousResearch/hermes-agent/main/plugin-catalog/README.md
- Installed Hermes source: `agent/web_search_provider.py`, `agent/secret_scope.py`, `hermes_cli/config.py`, `hermes_cli/plugins_cmd_install.py`.
