# Contributing to the Specfuse Orchestrator

The Specfuse orchestrator is a filesystem-based coordination layer for multi-agent software development. This repository holds the **upstream scaffolding** — agent configurations, shared rules, schemas, templates, and tooling — that downstream projects template-clone into their own private orchestration repos.

Two contributor paths exist, and the right one depends on which side of the upstream/downstream relationship you're on.

## I'm a downstream consumer with an improvement to share

If you're running the orchestrator on a real project (you template-cloned this scaffolding to your own private repo) and you've improved something — a clearer skill, a sharper rule, a better script, a fix to a shared schema — the contribution path is automated and documented:

```bash
./scripts/contribute-upstream.sh
```

The script reviews your downstream commits since the `UPSTREAM` anchor, identifies which touch scaffolding paths (the contributable subset), and produces clean path-scoped patch files for the ones you select. Private file diffs are dropped automatically; commit-message sanitization is flagged where likely needed. The full workflow — fork, `git am`, sanitize, push, open PR — is in [`docs/upstream-downstream-sync.md`](docs/upstream-downstream-sync.md) §"Contributing back to upstream".

What's contributable and what isn't:

- **Yes:** changes to `agents/`, `shared/`, `scripts/`, `docs/` (excluding `docs/walkthroughs/`), `project/README.md`, `README.md`, `LICENSE`, `NOTICE` — anything in the scaffolding that any project running the orchestrator could benefit from.
- **No:** anything project-specific (your features, events, inbox artifacts, integration plan, repo inventory, custom rules that only make sense for your product). The script's path scope keeps these out of the patches automatically; the rule is so that in writing PR descriptions you keep the framing project-agnostic.

## I want to work on the upstream itself

If you're contributing to the orchestrator scaffolding directly (not through a downstream), the relevant context is:

- [`docs/orchestrator-vision.md`](docs/orchestrator-vision.md) — goals and design rationale.
- [`docs/orchestrator-architecture.md`](docs/orchestrator-architecture.md) — the authoritative architecture document. When skills, configs, or other files conflict with the architecture, the architecture wins.
- [`docs/orchestrator-implementation-plan.md`](docs/orchestrator-implementation-plan.md) — the phased build plan; current state is "Phases 0–4 complete, Phase 4.5 onboarding interlude shipped, Phase 5 (generator feedback loop, config-steward) is the remaining build phase."
- [`docs/walkthrough-planning-conventions.md`](docs/walkthrough-planning-conventions.md) — the structural pattern for walkthrough planning if you're scoping a new phase.

Substantive changes to operational-agent surfaces (specs, PM, component, QA at frozen v1) require architectural justification per each agent's `version.md` freeze declaration. Phase 5+ work should follow the pattern established by Phases 1–4: work-unit-scoped commits, walkthrough at end of phase, retrospective, freeze.

## Commit message conventions

Match the existing pattern (see `git log --oneline`):

```
<type>(<scope>): <imperative summary>

<optional longer body, wrapped at ~80 columns>

Co-Authored-By: ...
```

Types observed in the repo:

- `feat(<scope>):` — new feature, skill, or capability
- `fix(<scope>):` — bug fix
- `chore(<phase-N>):` — phase-process work (walkthroughs, retrospectives, freezes)
- `docs:` or `docs(<scope>):` — documentation

Scope is typically the agent role (`specs`, `pm`, `component`, `qa`, `onboarding`) or the area (`scripts`, `phase-N`).

## Validation

Any change touching schemas, events, or frontmatter formats must round-trip through the validators:

```bash
python3 scripts/validate-event.py --file events/<file>.jsonl
python3 scripts/validate-frontmatter.py --file features/<file>.md
```

The walkthrough log artifacts in `docs/walkthroughs/phase-N/` are the existing test corpus — schema changes that break them require an architectural justification in the same commit.

## License

This project is licensed under Apache 2.0. By contributing, you agree your contributions are licensed under the same. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Questions

Open an issue on the upstream repo. The `docs/` directory is the authoritative reference for any "how does this work" question; if it doesn't answer your question, that itself is a documentation issue worth filing.
