# cspIngestionServiceSchema — Package Plan

See the [root plan](../PLAN.md) for overall architecture and cross-package decisions.

## What this package does

Small, dependency-light Python package holding the **internal CSP event schema** — the single normalized shape that `cspIngestionService` produces (from either `application/csp-report` or `application/reports+json`) and that `cspIngestionServiceLambdas` and `cspIngestionServiceApi` consume. Exists so the three repos share one schema definition instead of three independently-maintained copies that can drift.

Not deployed anywhere itself — it's a library dependency, not a service. No CDK stack owns it.

**Repo visibility: public** (the one exception to "all repos private"). Originally created private, but GitHub Actions' default token can't clone a private repo across repo boundaries even within the same account — every consuming repo's CI failed on `pip install` until this was made public. The alternative (a fine-grained PAT stored as a secret in every consumer) was rejected as unnecessary token-management overhead for a package that's just field names — no secrets, no infra topology, nothing sensitive.

## Distribution mechanism

Git-tag-pinned pip dependency over HTTPS (works unauthenticated now that the repo is public), not a private package registry (e.g. AWS CodeArtifact). Each consuming repo's `pyproject.toml` points at a specific tag:

```
csp-ingestion-schema @ git+https://github.com/rohitnagtilak92-maker/cspIngestionServiceSchema.git@v0.1.1
```

Chosen over CodeArtifact for simplicity — no new AWS infra (a CodeArtifact domain/repository, publish credentials in each repo's CI, auth config for local dev) for what is currently a small, low-churn schema. Revisit if the number of shared packages grows or publish/consume friction becomes real.

## Structure

```
cspIngestionServiceSchema/
├── src/csp_ingestion_schema/
│   ├── __init__.py
│   └── event.py        # the internal CSP event model (Pydantic)
├── pyproject.toml
└── .github/workflows/   # lint/test + tag-triggered nothing-to-publish (git tag IS the release)
```

## Steps

1. ✅ Scaffold `pyproject.toml`, `src/csp_ingestion_schema/event.py`
2. ✅ Define `CspViolationEvent` as a Pydantic `BaseModel`: normalized fields from both `csp-report`/`reports+json` formats, plus the enrichment fields the collector adds itself (`app_id`, app name, environment, AWS region, collector service version, customer `release`, request ID, receive timestamp, client IP)
3. ✅ Unit tests: construction from both formats, round-trip serialization, unknown-field rejection, required-field validation
4. ✅ CI: lint/test on PR
5. ✅ Tagged `v0.1.0`, then `v0.1.1` (made `original_policy` optional — real-world reports don't always include it, caught by `cspIngestionService`'s integration tests)
6. ✅ `cspIngestionService` depends on this package at `v0.1.1`; `cspIngestionServiceLambdas`/`cspIngestionServiceApi` will when they're built

## Open items owned by this package

- Versioning policy: does a schema change bump the tag and require all three consumers to update in lockstep, or does the model need to tolerate old-consumer/new-producer skew (e.g. new optional fields only)? Given all three repos deploy somewhat independently, additive-only changes within a major version is the likely rule — not yet formalized
