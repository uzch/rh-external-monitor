# Product

## Seller problem

Enterprise sellers have a large account population, uneven internal activity, and too much external information to review manually. They need a scoped, explainable shortlist and a clear next question to validate with the account team.

## Product promise

For a selected GEO, region, pod, territory, or account, produce a reusable portfolio artifact that says which accounts need attention, what internal evidence supports that ordering, what deeper context is available, and what remains uncertain.

## Views

Portfolio View is the scope-level triage surface. Account View is the drill-down surface. Both are rendered from the same validated JSON artifact so that filtering and presentation do not introduce unreproducible business logic.

## Guardrails

Internal facts, external public evidence, and agent interpretation are separate. The product does not turn a signal into customer intent, opportunity, fit, demand, renewal, deployment, or ownership.

## Implemented versus planned

Implemented in this repository: Enterprise Accounts registry loader, scope resolution logic, batch-query orchestration guidance, deterministic prioritization guidance, bounded MCP enrichment guidance, JSON schema, example artifact, validator, and HTML renderer.

Planned or integration-dependent: a Sheets writer, a public-signal connector, and a hosted interactive application.
