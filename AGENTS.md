# Development guidance

## Planning source of truth

GitHub issues and milestones in `zchrykng/hermes-plugin-kagi` are authoritative for
future development. Start with https://github.com/zchrykng/hermes-plugin-kagi/issues/4.

Before implementation, read the relevant issue, its dependencies, acceptance criteria
and linked current official API documentation. Update scope, decisions, priorities
and progress in GitHub; do not recreate a competing roadmap in repository files.
`PROJECT.md` contains stable architecture/owner decisions, `README.md` documents
shipped behavior, and `AUDIT.md` preserves historical evidence only.

Link implementation PRs to their issues. Use closing keywords only when acceptance
criteria are fully verified; reference partial work without closing the issue.
Keep the central roadmap checklist aligned with verified issue status.

## Guardrails

Preserve scoped credentials, native Hermes contracts, root packaging and backend
settings. No active-profile migrations, gateway restarts, paid API tests, release
publication or upstream catalogue submission merely because an issue exists: follow
its approval conditions and current user authorization. Catalogue submissions remain
manual and owner-approved; upstream maintainers review every exact-SHA pin.

## Verification

Use an isolated home and a real Hermes source/runtime as documented in README.md.
Run `scripts/run_tests.py` and applicable Doctor/catalogue checks. Distinguish fixture
results from live API and billing evidence. Do not install test dependencies into
the user's active Hermes environment.
