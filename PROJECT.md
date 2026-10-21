# Kagi

## Goal
A single Hermes plugin named `kagi` covering Kagi's documented API functionality wherever it has a useful, safe Hermes integration. Keep ordinary search and extraction on Hermes's native tools; expose specialized capabilities as explicit Kagi tools rather than distorting the native contracts. No Hermes core fork and no instruction-only routing.

## Identity and compatibility
- Plugin manifest name: `kagi`.
- Provider ID and managed install/discovery key: `kagi`.
- Distribution: repository-root `plugin.yaml`, `__init__.py`, `provider.py`, `LICENSE`, and `README.md`; no catalog `subdir`. Relative entry-point imports work independently of checkout basename.
- Keep existing checkout directories stable for desktop/project links; the public repository is `hermes-plugin-kagi` and the plugin product is Kagi.
- Keep `web.search_backend: kagi` working throughout expansion.

## Current implementation and evidence
Search-only v1 backend implemented. Offline tests exercise the actual Hermes loader and profile-secret isolation. A development installation has completed a live search with runtime logs explicitly recording `Web search via kagi` and successful tool completion. This is routing evidence, not a billing audit. Search is the only implemented capability; everything below is planned.

## API inventory and proposed Hermes mapping
The current v1 OpenAPI bundle advertises only POST `/search` and POST `/extract`. Kagi's broader API portal separately documents Enrichment, Universal Summarizer, FastGPT, and the free Small Web feed. Do not mistake the OpenAPI bundle for the complete API inventory. The additional products' docs currently show v0 endpoints and Bot auth; verify each product's current auth, availability, and account entitlement independently before implementation. Do not apply v1 Bearer auth blindly to older products.

| Capability | Hermes surface | Scope and constraints | Priority |
| --- | --- | --- | --- |
| General web search | Existing `web_search` backend | Preserve the working contract and default route | Implemented |
| Page extraction | Existing `web_extract` backend | v1 batch URL-to-markdown; per-URL errors, stable input mapping, standard content budget and timeout integration | Next |
| Specialized search | Proposed `kagi_search` tool, same client | Images, videos, news, podcasts; preserve workflow-specific result groups and metadata | Next |
| Advanced search controls | Proposed `kagi_search` parameters plus documented plugin defaults | Saved/inline lenses, include/exclude sites and keywords, file type, region, dates, safe search, supported personalization; validate combinations and precedence | Next |
| Pagination and search-plus-extract | Explicit `kagi_search` options | Page selection, result limits, extraction count and timeout; disclose extra cost and never auto-fetch all pages | Next |
| Enrichment | Proposed `kagi_enrich` tool | Teclis web and TinyGem news; clearly labeled niche indexes, not substitutes for general search | Later |
| Universal Summarizer | Proposed `kagi_summarize` tool | URL or supplied text, paragraph/takeaway output, supported engines and target language, explicit cache/privacy controls | Later |
| FastGPT | Proposed `kagi_answer` tool | Search-grounded generated answer with references; distinguish generated output from source excerpts and index results | Later |
| Small Web feed | Proposed `kagi_smallweb` tool | Free bounded RSS discovery; dates, links, deduplication and safe XML parsing; no credential header on public feed | Later |

Tool names are design proposals, not registered commands yet. Reconfirm supported enum values and parameter limits from each source before writing schemas. Preserve useful response metadata such as dates, image URLs and citations; do not flatten specialized responses into misleading general web results. Start with JSON output; evaluate experimental API Markdown output only if it adds value over stable structured results.

## Architecture
1. A shared internal HTTP/client layer for timeouts, redaction, bounded payloads, trace IDs and structured errors. Keep auth/version routing product-specific.
2. A native `WebSearchProvider` adapter for generic search and, once implemented, extraction.
3. Explicit plugin tools for capabilities the generic `web_search(query, limit)` and `web_extract(urls, ...)` contracts cannot express.
4. Read-only availability gates and profile-aware credential lookup. No launch-profile key fallback when serving another profile.
5. Optional feature gates for specialized tools; implementing extraction must not automatically switch the user's `web.extract_backend`.
6. Keep the backend plugin manifest while investigating and testing mixed provider/tool registration through the actual Hermes loader. If the loader restricts backend plugins, resolve the packaging design before adding tools, while preserving one public product identity.

## Milestones and acceptance gates
### 1. Identity and scope
Source manifest identity is `kagi`; root distribution and installed-layout loader regression tests are in place. Preserve existing active installations and settings unless migration is separately approved. No gateway restart is part of this source edit; in-memory metadata may retain its old label until reload.

### 2. Native extraction and client foundation
Implement v1 extraction with offline test-first slices and actual Hermes loader/dispatcher checks. Cover batch limits, partial failures, URL mapping, timeouts, malformed responses, and content budgets. Do not label it implemented until the standard tool route is exercised. Run an explicitly approved live extraction test before recommending activation.

### 3. Full search API features
Implement specialized workflows and advanced controls behind an explicit tool. Reuse the client and default native route, without changing the generic Hermes tool schema. Include supported request fields and useful response groups from the current OpenAPI, account setting inheritance guidance, and paid extraction controls. Validate specialized responses and real tool registration.

### 4. Remaining useful APIs
Implement enrichment, summarization, FastGPT and Small Web incrementally, each with its own contract/auth review, unit tests, fixtures clearly labeled as fixtures, and separately approved live smoke test. Document unavailable/deprecated operations rather than promising unsupported behavior.

### 5. Release readiness
Provide packaging, CI, supported Hermes-version checks, migration/rollback instructions, profile-safe setup, per-capability configuration, and clear cost/privacy guidance. Publishing a repository or catalog listing is a separate approval step.

## Safety, cost and observability
- No automatic paid retries, pagination, search-time extraction, summarization or FastGPT chaining. Require explicit tool options/requests for additional work.
- Apply Hermes URL/security policy to remote extraction and summarization; uploading user text is a separate data disclosure, not ordinary search.
- Summaries and FastGPT answers must remain explicitly labeled generated content; never represent them as verbatim extracted pages.
- Never log keys or raw sensitive request/response bodies. Include safe provider identity, operation, cache status, duration and trace identifiers where available to verify routing without guessing from results.
- Define timeouts, maximum pages/URLs, response-size caps and per-operation error behavior. Preserve partial successes where the API supports them.
- Credential storage stays in profile secret storage; nonsecret settings use Hermes config commands. Inspect provider config conventions before selecting a namespace.
- Offline tests cannot establish live endpoint availability, billing behavior or account permissions. Keep those claims separate.

## Out of scope unless Kagi exposes a documented API
Browser scraping of authenticated Kagi products, account/billing/key administration, browser extensions and Orion management. Do not invent Assistant, translation, or other product endpoints. Revisit scope when official APIs are published.

## Sources
- Hermes provider contract: https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin
- Hermes plugin lifecycle: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- Kagi API inventory: https://help.kagi.com/kagi/api/overview.html
- v1 API and OpenAPI: https://kagi.com/api/docs and https://kagi.com/api/docs/_bundle/openapi.json
- Enrichment: https://help.kagi.com/kagi/api/enrich.html
- Summarizer: https://help.kagi.com/kagi/api/summarizer.html
- FastGPT: https://help.kagi.com/kagi/api/fastgpt.html
- Small Web: https://help.kagi.com/kagi/api/smallweb.html
- Keys and pricing: https://kagi.com/api/keys and https://kagi.com/api/pricing
