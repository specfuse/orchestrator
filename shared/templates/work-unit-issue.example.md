<!--
Fully-worked example of shared/templates/work-unit-issue.md v1.0.

This is a fictional task (FEAT-2026-0042/T07) used consistently across
the component agent skills as a running example. It is not a real
feature in this repo. Use it as a reference for the shape of a
well-formed work unit issue — what each section looks like when
filled by a competent PM agent for a realistic implementation task in
a hypothetical API component repo `clabonte/api-sample`.

HTML comments remain only to annotate the example; in a real issue,
all HTML comments are deleted before posting.
-->

```yaml
correlation_id: FEAT-2026-0042/T07
task_type: implementation
autonomy: review
component_repo: clabonte/api-sample
depends_on: [T03]
generated_surfaces:
  - _generated/Controllers/OrdersController.cs
```

## Context

This task is part of **FEAT-2026-0042 — Order intake validation**, which brings the `POST /orders` endpoint into conformance with the published OpenAPI contract. The feature's scope covers request-body validation, structured error responses, and persistence-layer guardrails across the API and persistence components.

T07 owns the API-side handler logic for one specific gap: rejecting requests whose body omits the `email` field with a `400` response, instead of silently coercing the value to `null` and producing a `500` when the persistence layer's NOT NULL constraint fires. T03 (which this task depends on) extracted the shared `OrderRequestValidator` the handler now delegates into; T07 wires email presence into that validator and verifies the end-to-end behavior.

- Feature registry: `features/FEAT-2026-0042.md`
- OpenAPI reference: `product/openapi.yaml:120-158` (the `POST /orders` operation and its request schema)
- Behavior spec: `product/features/order-intake-validation.md` §"Email presence"

## Acceptance criteria

1. A `POST /orders` request whose JSON body does not contain an `email` field produces a `400 Bad Request` response with body `{ "error": "missing_required_field", "field": "email" }`.
2. A `POST /orders` request whose `email` field is present but is the empty string produces the same `400` response as above — empty-string must be distinguished from missing for API ergonomics, not conflated.
3. A `POST /orders` request with a non-empty `email` is accepted by the validator and reaches the persistence layer unchanged (regression: prior behavior for valid requests is not affected).
4. The rejection is emitted by `OrderRequestValidator` rather than inline in the controller, so the same logic is reused by the `PATCH /orders/{id}` handler without duplication.
5. A unit test in `ApiTests/OrdersControllerTests.cs` covers each of the three cases above (missing, empty, valid), and each test asserts the exact response shape from criterion 1 where applicable.

## Do not touch

- `_generated/Controllers/OrdersController.cs` beyond the specific override authorized for this task (see `/overrides/FEAT-2026-0042-T07-orders-controller-validator-hook.yaml`). Any other change to a `_generated/` path is a spec issue, not an edit.
- Files owned by T08 (`ApiTests/OrdersControllerTests_Patch.cs`) and T11 (`Persistence/OrderRepository.cs`) — both are in flight in parallel; do not merge changes across branches.
- `/business/` in the product specs repo (unreadable by agents).
- Branch protection configuration on `clabonte/api-sample` (`.github/settings.yml` and any workflow declared as a required check).
- Any secret (`.env`, `*.pem`, `*.key`, `appsettings.Production.json` if it carries credentials in this repo's layout).

## Verification

Per-task commands, run from `clabonte/api-sample` root. These are in addition to the six mandatory gates declared in `.specfuse/verification.yml` (see `agents/component/skills/verification/SKILL.md`).

```sh
dotnet test ApiTests --filter "FullyQualifiedName~OrdersControllerTests" --no-build --verbosity normal
dotnet test ApiTests --filter "FullyQualifiedName~OrderRequestValidatorTests" --no-build --verbosity normal
grep -F "email" src/Validators/OrderRequestValidator.cs
```

## Escalation triggers

- If the generated `OrdersController.cs` has structurally changed since the override was authorized such that the override's hook no longer applies cleanly, escalate with `override_expiry_needs_review` — do not rewrite the hook speculatively.
- If the OpenAPI schema in `product/openapi.yaml` does not in fact mark `email` as required (verify before implementing), escalate with `spec_level_blocker` — the spec is the source of truth for validation behavior, not the current runtime.
- If T03's `OrderRequestValidator` does not expose an extension seam for presence checks (which T03's acceptance criteria claimed it would), escalate with `spec_level_blocker` against T03's closure rather than working around it in T07.
- None beyond the four universal triggers in `shared/rules/escalation-protocol.md` apply otherwise.
