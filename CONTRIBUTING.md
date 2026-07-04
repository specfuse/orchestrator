# Contributing to the Specfuse Orchestrator

The Specfuse orchestrator is a filesystem-based coordination layer for multi-agent software development. This repository is the source for the `specfuse-orchestrator` pip package — agent configurations, shared rules, schemas, templates, and the CLI (`init` / `upgrade`) that projects install from PyPI and use to scaffold their own orchestration repos.

Contributions are normal pull requests against this repository. If you've improved something — a clearer skill, a sharper rule, a fix to a shared schema, a CLI fix — branch, commit, and open a PR here.

## Working on the package

The relevant context is:

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
specfuse-validate-event --file events/<file>.jsonl
specfuse-validate-frontmatter --file features/<file>.md
```

The walkthrough log artifacts in `docs/walkthroughs/phase-N/` are the existing test corpus — schema changes that break them require an architectural justification in the same commit.

## License

The `specfuse-orchestrator` package is licensed under Apache 2.0. By contributing to this repository, you agree your contributions are licensed under the same terms. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

An orchestration repo a user creates with `specfuse-orchestrator init` is their own new git repo, licensed however they choose — see [`README.md`](README.md) §"Licensing".

## Questions

Open an issue on the repo. The `docs/` directory is the authoritative reference for any "how does this work" question; if it doesn't answer your question, that itself is a documentation issue worth filing.
