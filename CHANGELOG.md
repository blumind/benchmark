# CHANGELOG — BluMind Benchmark

Benchmark version history. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioned according to [SemVer](https://semver.org/) adapted to a benchmark context:

- **MAJOR** (`v1.0.0` → `v2.0.0`): changes to the rubric or scored fields. Scores **are not comparable** between major versions.
- **MINOR** (`v1.0.0` → `v1.1.0`): new cases, families or documentation are added. Previous scores **remain comparable**.
- **PATCH** (`v1.0.0` → `v1.0.1`): errata, clarifications, never affects calculations.

Each version is frozen in its folder (`cases/v1.0/`, `cases/v2.0/`, …) and is not overwritten when the next one is published.

This CHANGELOG documents **system changes** (rubric, schemas, cases, scripts, documentation). New model evaluations are tracked in `subjects/registry.yaml` and in the snapshots under `results/history/`, not here.

---

## [Unreleased]

> Pre-release state of v1.0. Will be promoted to `[v1.0.0] — YYYY-MM-DD` when
> the `v1.0.0` git tag is pushed. Until then, every entry below describes a
> system change already merged into `main`.

### Added — Benchmark system

- **5 failure families** (`OXID`, `SCAL`, `FOUL`, `MECH`, `NOWE`) defined in
  [`system/families/v1.0/taxonomy.md`](system/families/v1.0/taxonomy.md), with
  stable codes guaranteed across future versions.
- **31 cases** under `cases/v1.0/`, one Markdown file per case, statements
  authored in Spanish to preserve operational authenticity.
- **Generic rubric (0–12, six criteria)** in
  [`system/rubric/v1.0/generic_rubric.md`](system/rubric/v1.0/generic_rubric.md),
  with case-type modulation (`Closed` / `Semi-closed` / `Open` / `Ambiguous`)
  and a two-tier automatic-fail system (`critical` / `recoverable`).
- **Aggregated metrics** (`P`, `s̄`, soft Brier, ECE with 10 fixed-width bins,
  `Q_final`, safety gate) formalised in
  [`system/rubric/v1.0/aggregated_metrics.md`](system/rubric/v1.0/aggregated_metrics.md).
- **Prompt template** in
  [`system/prompts/v1.0/prompt_template.md`](system/prompts/v1.0/prompt_template.md),
  identical across subjects and tracks.
- **JSON Schemas** under `system/schemas/v1.0/` covering: subject response,
  reviewer scoring (with optional PREMIUM `justification_long` field),
  case gold, ideal response, subject registry.
- **Sampling-policy split** (`classic` / `reasoning`) on a single public
  leaderboard with the mode annotated per row — rationale in
  [`docs/run_evaluation_design.md`](docs/run_evaluation_design.md) § 7.

### Added — Evaluation pipeline

- `scripts/run_evaluation.py` — multi-provider runner via LiteLLM, with
  retries, telemetry, and append-only response storage.
- `scripts/validate_response.py`, `scripts/validate_evaluation.py`,
  `scripts/validate_gold.py`, `scripts/validate_ideal_response.py`,
  `scripts/validate_registry.py` — strict schema validators.
- `scripts/compute_metrics.py` — deterministic aggregator producing
  `results/per_run.csv`, `results/metrics_per_subject.csv`,
  `results/metrics_per_family.csv`.
- `scripts/compute_operational.py` — telemetry aggregator producing
  `results/operational_per_subject.csv` and
  `results/operational_per_family.csv`.
- `scripts/build_leaderboard.py` — public Markdown leaderboard renderer,
  with dynamic family coverage and disqualified-subject section.

### Added — Public / commercial split

- `scripts/check_public_safety.py` — audit gate that detects and (with
  `--export`) strips PREMIUM content before publishing.
- `ideal_responses/v1.0/` placeholder folder for commercial-tier expert
  answers; per-case file contents are gitignored, only the schema is public.
- PREMIUM field `justification_long` added to
  [`system/schemas/v1.0/evaluation.schema.json`](system/schemas/v1.0/evaluation.schema.json),
  optional and intentionally omitted from the public export.
- New ideal-response schema and validator
  ([`system/schemas/v1.0/ideal_response.schema.json`](system/schemas/v1.0/ideal_response.schema.json),
  `scripts/validate_ideal_response.py`).
- `.gitignore` rules for `ideal_responses/v1.0/*.json` and the existing
  private-side patterns (`golds/`, `mappings/`, `sellos/`, secrets).

### Added — Documentation

- [`docs/methodology.md`](docs/methodology.md) — entry-point map linking
  to all authoritative sources.
- [`docs/findings_v1.0.md`](docs/findings_v1.0.md) — canonical v1.0
  findings report (~15 pages), authored by the BluMind Technical
  Committee, covering the safety-gate analysis, generational uplift,
  hypothesis quality, per-family weaknesses, calibration, cost and
  the explicit limitations of v1.0. Subject to a 7-day provider
  embargo prior to public release.
- [`docs/reviewer_guide.md`](docs/reviewer_guide.md) — reviewer scoring
  guide, including the *"Premium contributions for the commercial datasets"*
  section.
- [`docs/run_evaluation_design.md`](docs/run_evaluation_design.md) — design
  decisions for the runner (LiteLLM, secrets, retries, idempotency,
  telemetry, sampling policy).
- [`results/README.md`](results/README.md) — purpose, consumer and life
  cycle of every CSV under `results/`.

### Added — Initial evaluation set (subjects)

12 subjects evaluated against the 31 cases (`12 × 31 = 372 runs`), spanning
both sampling modes:

- **Reasoning track**: `claude-opus-4-7`, `gpt-5-5`.
- **Classic track**: `gpt-5`, `claude-opus-4-6`, `claude-haiku-4-5`,
  `gemini-2-5-pro`, `gemini-2-5-flash-lite`, `gemini-3-1-flash-lite`,
  `deepseek-v4-flash`, `mistral-medium-3`, `mistral-small-3`,
  `gpt-3-5-turbo` (legacy baseline).

The leaderboard is regenerated from these runs by `build_leaderboard.py` and
lives at [`results/leaderboard.md`](results/leaderboard.md). The safety gate
disqualifies any subject with ≥ 1 critical automatic fail.

### Scope clarification

- Project-level scope is **the entire water treatment sector** (potabilization,
  wastewater treatment, water reuse, industrial water, across membrane and
  non-membrane processes). v1.0 is the first acotated release on RO
  desalination.
- The leaderboard subtitle and reviewer-recruitment policy in
  [`README.md`](README.md) reflect this project / release separation.

### Deferred to v2.0+

The following capabilities are intentionally **not** in v1.0 and carry
explicit notes in their respective artifacts:

- **Reviewer registry binding** — `gold_author_id` and `gold_reviewer_id`
  currently accept any non-empty string; v2.0 binds them to a central
  reviewer registry for traceable inter-reviewer κ.
- **Weighted / ranked main hypotheses** for partial credit in
  `gold.accepted_main_hypotheses`.
- **Per-field length limits** in `response.schema.json` (only
  `minLength: 1` is enforced today).
- **Digital certification seal** (`scripts/emit_seal.py`,
  `docs/seal_reglamento.md`).
- **Tool-augmented track** (no RAG / function calling in v1.0).
- **Multi-reviewer per (case, subject, run)** with inter-reviewer
  consolidation.
- **Sub-sectors beyond RO desalination**: potabilization, wastewater
  treatment, water reuse, industrial water, other membrane processes
  (UF, MF, NF, EDR, EDI) and non-membrane processes.
- **Pretreatment, post-treatment, intake works, concentrate disposal and
  auxiliary CIP equipment** within RO desalination plants.

---

---

## Backward compatibility policy

- An evaluated response is bound to the benchmark version via the mandatory `benchmark_version` field in `response.schema.json`. This version implicitly binds the taxonomy, rubric, prompt and schema versions in force at that moment (principle of "single package per benchmark version").
- The leaderboard always displays the reference version of the score (e.g. "Pass rate 0.73 [v1.0]").
- When a MAJOR version (`v2.0`) is released, the v1.0 leaderboard is preserved as a frozen history under `results/history/`.

---

## Link conventions

The `[1.0.0]`-style links at the bottom of this file point to the corresponding git tags once the release is published:

<!-- [Unreleased]: https://github.com/<org>/blumind-benchmark/compare/v1.0.0...HEAD -->
<!-- [1.0.0]: https://github.com/<org>/blumind-benchmark/releases/tag/v1.0.0 -->
