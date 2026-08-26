# cspIngestionServiceSchema — Package Plan

See the [root plan](../PLAN.md) for overall architecture and cross-package decisions.

## What this package does

Small, dependency-light Python package holding the **internal CSP event schema** — the single normalized shape that `cspIngestionService` produces (from either `application/csp-report` or `application/reports+json`) and that `cspIngestionServiceLambdas` and `cspIngestionServiceApi` consume. Exists so the three repos share one schema definition instead of three independently-maintained copies that can drift.

Not deployed anywhere itself — it's a library dependency, not a service. No CDK stack owns it.

## Distribution mechanism

Git-tag-pinned pip dependency, not a private package registry (e.g. AWS CodeArtifact). Each consuming repo's `pyproject.toml` points at a specific tag:

```
cspingestionserviceschema @ git+ssh://git@github.com/rohitnagtilak92-maker/cspIngestionServiceSchema.git@v1.0.0
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

1. Scaffold `pyproject.toml` (package name `csp-ingestion-schema` or similar), `src/csp_ingestion_schema/event.py`
2. Define the internal event model as a Pydantic `BaseModel`: normalized fields from both `csp-report`/`reports+json` formats, plus the enrichment fields the collector adds itself (`app_id`, app name, environment, AWS region, collector service version, customer `release` — from the optional `?release=` query param, `None` if unset, request ID, receive timestamp, client IP) — this is the schema `cspIngestionService` produces and pushes to SQS as JSON
3. Unit tests: round-trip serialization, and that both source report formats validated in `cspIngestionService`'s `normalize.py` produce a valid instance of this model
4. CI: lint/test on PR
5. Tag `v1.0.0` once the shape is stable enough for the three consumers to pin against
6. Update `cspIngestionService`, `cspIngestionServiceLambdas`, `cspIngestionServiceApi` to depend on this package at that tag, removing any local duplicate model definitions

## Open items owned by this package

- Exact field list/types for the internal event model (drafted alongside `cspIngestionService`'s `normalize.py` — see that repo's plan)
- Versioning policy: does a schema change bump the tag and require all three consumers to update in lockstep, or does the model need to tolerate old-consumer/new-producer skew (e.g. new optional fields only)? Given all three repos deploy somewhat independently, additive-only changes within a major version is the likely rule — not yet formalized
- Whether this warrants its own private GitHub repo (as planned) or could instead live as a subdirectory of one of the three consumers — repo-per-concern was chosen for consistency with the rest of this project's structure
