# Spec: bootstrap

See also `docs/ARCHITECTURE.md` and JSON schemas under `schemas/`.

## Responsibilities

Documented contract for the `bootstrap` subsystem. Implementation must satisfy the acceptance criteria below and remain aligned with `AGENTS.md`.

## Inputs

- Organization configuration (`org.yaml`)
- Authorized credentials / scopes
- Published knowledge version (where applicable)

## Outputs

- Validated, provenance-bearing records or API responses
- Explicit failure / gap reports (never silent skip of required work)

## Acceptance criteria

1. Behavior is deterministic for the same inputs and revision where claimed.
2. Partial failures are visible and do not imply full success.
3. Permissions are enforced; secrets are never logged.
4. Tests under `tests/` cover happy path and key failure modes.
5. Contract changes update schemas, migrations, docs, and tests together.
