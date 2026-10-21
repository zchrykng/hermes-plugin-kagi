# Kagi: architecture and project decisions

## Development source of truth

**GitHub issues and milestones are the authoritative roadmap.** Start with
[roadmap #4](https://github.com/zchrykng/hermes-plugin-kagi/issues/4), then read
the relevant work issue, its dependencies and acceptance criteria.

- [Search-only catalogue readiness](https://github.com/zchrykng/hermes-plugin-kagi/milestone/1)
- [Native extraction and full search](https://github.com/zchrykng/hermes-plugin-kagi/milestone/2)
- [Additional Kagi APIs](https://github.com/zchrykng/hermes-plugin-kagi/milestone/3)
- [All work issues](https://github.com/zchrykng/hermes-plugin-kagi/issues)

Milestones are planning groups, not delivery-date promises. Update scope, priorities,
dependencies, decisions and completion status on GitHub first. Link implementation
PRs to their issues; close work only after its acceptance criteria are verified.
Do not maintain a second mutable roadmap here. `AUDIT.md` is historical evidence;
its unresolved follow-ups now have GitHub issues. `README.md` describes shipped behavior.

## Product goal

One plugin named `kagi` for useful functionality exposed by Kagi's documented APIs.
Ordinary search and extraction use native Hermes provider surfaces; specialized
operations use explicit, accurately declared optional tools. Do not distort native
contracts, rely on instruction-only routing, or fork/patch Hermes core.

## Identity and distribution

- Plugin manifest name, provider ID and managed installation key: `kagi`.
- Repository: https://github.com/zchrykng/hermes-plugin-kagi.
- Root distribution: `plugin.yaml`, `__init__.py`, `provider.py`, `LICENSE`, `README.md`.
  No catalogue subdirectory; imports must work independently of checkout basename.
- Legacy copies use `web/kagi`. Migration preserves settings/local changes, avoids
  duplicate registration, backs up outside the scanned plugins tree and retains
  rollback. Execution is tracked in [#9](https://github.com/zchrykng/hermes-plugin-kagi/issues/9).
- Keep backend ID `kagi` stable and existing desktop checkout links intact. Source
  changes do not migrate an installation, change backend settings or restart gateways.

## Approved release decisions

- MIT license.
- Initial catalogue release is search-only; planned tools are not implemented merely
  because they are on the roadmap.
- Manual release submission with owner approval; upstream maintainers review every
  exact-SHA catalogue pin. See [#10](https://github.com/zchrykng/hermes-plugin-kagi/issues/10)
  and [#11](https://github.com/zchrykng/hermes-plugin-kagi/issues/11).
- Active legacy migration is approved after tests, with backup/rollback. Paid smoke
  tests require separate approval.
- No self-updater, automatic catalogue PRs on each push, or automatic upstream merge.

## Architectural and safety invariants

1. Use public Hermes registration/provider APIs, scoped secrets and documented
   nonsecret settings conventions. Availability checks remain read-only and
   network-free; served profiles must not borrow launch-profile credentials.
2. Check current contract, API version, authentication, entitlement and cost per
   product. Kagi's API portal includes products absent from its v1 OpenAPI bundle;
   do not assume a shared authentication scheme across all products.
3. Bound requests/responses, sanitize errors and redact observability. Never log
   keys or sensitive bodies. Socket timeouts are not total elapsed-time deadlines.
4. No unrequested paid retries, pagination, extraction, summarization or answer
   chaining. Additional operations must be explicit with cost/data disclosures.
5. Apply Hermes URL/security policy to remote extraction and summarization. Uploading
   supplied text is a separate disclosure; generated summaries/answers are not verbatim
   extracted pages. Preserve useful metadata and citations.
6. Implementing a capability must not change the user's backend selection. Verify
   mixed provider/tool registration through the real loader before relying on it.
7. Offline fixtures, loader/dispatcher tests, managed installation, live requests and
   billing are distinct evidence. Require separate approval before paid API calls.

## Out of scope

Authenticated product scraping, account/billing/key administration, Orion/browser
extension management, and invented Assistant/translation endpoints. Revisit through
an explicit issue when Kagi publishes a relevant official API.

## Technical references

- [Hermes provider contract](https://hermes-agent.nousresearch.com/docs/developer-guide/web-search-provider-plugin)
- [Hermes plugin development](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
- [Catalogue submission](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission)
- [Kagi API inventory](https://help.kagi.com/kagi/api/overview.html)
- [Kagi API reference](https://kagi.com/api/docs)
- [Kagi OpenAPI](https://kagi.com/api/docs/_bundle/openapi.json)

Per-feature implementation details and current status belong in the linked GitHub
issues, not a parallel plan in this document.
