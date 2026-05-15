# BluMind Benchmark

> The reference benchmark for measuring the technical competence of AI models in the water sector.

BluMind Benchmark evaluates the ability of AI models (LLMs and expert systems) to diagnose and reason about real operational problems in the water sector.

This repository contains the **public** part of the benchmark: open cases, rubric, schemas, evaluation scripts and leaderboard. The private part (golds, closed cases, certification seals) is managed outside this repository.

> **Language policy.** Public-facing artifacts (README, rubric, schemas, taxonomy, documentation) are authored in English. Case statements and gold answers in v1.0 are authored in Spanish to preserve the operational authenticity of plant reports from Spanish-speaking utilities. Translation is part of the evaluation.

---

## Scope (v1.0)

BluMind Benchmark v1.0 covers operational failures within the **reverse-osmosis (RO) system** of desalination plants — from the **high-pressure pump inlet** to the **exit of the pressure tubes in the racks**.

**In scope**: seawater RO (SWRO) and brackish water RO (BWRO) plants; HP pumps, high-pressure piping and valves, energy-recovery devices when integrated in the RO skid, pressure vessels, membrane elements, and permeate/concentrate manifolds at the rack exit.

**Out of scope for v1.0** (deferred to future versions): pretreatment, post-treatment, intake works, concentrate disposal, and auxiliary CIP equipment within RO desalination plants.

BluMind's long-term scope is **the entire water treatment sector** — including potabilization, wastewater treatment, water reuse, and industrial water, across membrane (RO, UF, MF, NF, EDR, EDI) and non-membrane processes. v1.0 acts as the first acotated release on RO desalination; each subsequent version will open a new sub-sector or expand an existing one.

See [`CHANGELOG.md`](CHANGELOG.md) for the deferred list per release.

**Per-subject sampling, single leaderboard.** v1.0 ranks every model in a single public table, with the sampling configuration shown as an annotation column on each row — in line with mainstream evaluation practice (HELM, MMLU-Pro, GPQA, Artificial Analysis). Two sampling modes are supported:

- **Classic** — the original v1.0 contract: `temperature = 0` is sent to the provider. Covers all models that accept this contract (GPT-5, Claude Opus 4.6, Gemini 2.5 Pro, Mistral, DeepSeek, GPT-3.5 Turbo, …).
- **Reasoning** — for frontier reasoning models that reject `temperature` (e.g. OpenAI GPT-5.5, Anthropic Claude Opus 4.7). The runner omits `temperature`/`top_p`/`top_k` and uses a single portable knob (`reasoning_effort`), which LiteLLM translates into each provider's native control.

Each subject declares its mode in `subjects/registry.yaml` (`sampling_policy.kind`), and every published response records it (`track`). See [`docs/run_evaluation_design.md`](docs/run_evaluation_design.md) § 7 for the full rationale.

---

## Quick links

- **Public leaderboard**: [https://benchmark.blumind.es](https://benchmark.blumind.es) *(pending)*
- **Methodology**: [`docs/metodologia.md`](docs/metodologia.md) *(pending)*
- **Submit a model for evaluation**: [`docs/submission_guide.md`](docs/submission_guide.md) *(pending)*
- **Join as an expert reviewer**: [`docs/reviewer_guide.md`](docs/reviewer_guide.md) *(pending)*
- **License**: [`LICENSE`](LICENSE)

---

## What BluMind Benchmark measures

Each case presents a real operational problem (symptoms, sensor readings, recent history) and asks the subject for a JSON-structured response with seven fields (six scored + one for calibration):

| Field | Meaning |
|---|---|
| `main_hypothesis` | Most likely root cause (not a symptom). |
| `key_signals` | Which connected variables support the hypothesis. |
| `alternatives` | Technically plausible rival hypotheses. |
| `requested_data` | The "trigger" datum that would discriminate between hypotheses. |
| `recommended_action` | Safe, specific action, compatible with manuals. |
| `decision_change_condition` | Counterfactual reasoning: under which signal would the diagnosis change. |
| `confidence` | Value 0-100 used for longitudinal calibration (not scored per case). |

Each response is scored 0-12 against a **rubric** published in this repository, and compared against a private **gold** reviewed by a second senior expert (peer review). The final classification is **Pass / Conditional / Fail** according to the thresholds: **Pass** ≥ 10, **Conditional** 7-9, **Fail** < 7.

A **critical automatic fail** is triggered when the response recommends an action that would put plant integrity or operator safety at risk, disqualifying the response regardless of the numeric score.

Aggregated metrics per evaluated subject: Pass rate, mean clipped score 0-12, Brier score, ECE (Expected Calibration Error), and `Q_final` (50/50 composite of Pass rate and normalised mean score). A subject with **any** critical automatic fail in the corpus is **disqualified** from the leaderboard regardless of its other numbers (safety gate). Full formulas, justifications and binning conventions: [`system/rubric/v1.0/aggregated_metrics.md`](system/rubric/v1.0/aggregated_metrics.md).

---

## Public / private architecture

BluMind Benchmark is deliberately **hybrid**: credibility comes from the public side, defensible revenue comes from the private side.

```
 ┌─────────────────────────────────────────┐      ┌──────────────────────────────┐
 │         PUBLIC (this repo)              │      │           PRIVATE            │
 ├─────────────────────────────────────────┤      ├──────────────────────────────┤
 │ • Generic rubric                        │      │ • All golds                  │
 │ • JSON Schemas                          │      │ • v2.0 closed cases          │
 │ • Family taxonomy                       │      │ • v3.0 cases (majority)      │
 │ • v1.0 cases (30 cases)                 │      │ • reviewer_id → real name    │
 │ • v2.0 cases (40 public of 80)          │      │ • SFT / RLHF datasets        │
 │ • v3.0 cases (60 public of 300)         │      │ • Seal regulations           │
 │ • Lab responses                         │      └──────────────────────────────┘
 │ • Leaderboard + aggregated metrics      │
 │ • Evaluation scripts                    │
 └─────────────────────────────────────────┘
```

**Fundamental rule**: **golds are never published**, not even for public cases. Publishing a gold is equivalent to publishing exam answers before the exam.

---

## Repository structure

```
blumind-benchmark/
├── system/                   # Immutable infrastructure per benchmark version
│   ├── rubric/v1.0/          # Generic rubric (scoring framework)
│   ├── schemas/v1.0/         # JSON Schemas (response, evaluation, gold, ideal_response, registry)
│   ├── prompts/v1.0/         # Prompt template sent to the subject
│   └── families/v1.0/        # Taxonomy of the 5 failure modes
├── cases/                    # Case statements (public part)
│   └── v1.0/                 # 30 v1.0 cases, all public
├── subjects/
│   └── registry.yaml         # Central registry of evaluated subjects
├── responses/                # Subject responses (append-only)
├── scoring/                  # Human scoring (append-only)
├── ideal_responses/          # Canonical expert-authored answers per case
│   └── v1.0/                 # (schema public; contents premium — see § 10 of docs/reviewer_guide.md)
├── results/                  # Derived outputs (CSVs); see results/README.md
├── scripts/                  # Automation (Python)
├── web/                      # Public site (GitHub Pages)
└── docs/                     # Documentation for labs, reviewers, utilities
```

**Folders absent by design in the public repo:**

- `golds/` — lives in a separate private repo (`blumind-benchmark-golds`).
- `mappings/` — the `reviewer_id` to real-name mapping lives outside this repo.
- `sellos/` — issuance of signed certificates, outside the public repo.
- `ideal_responses/v1.0/*.json` — file **contents** are not committed to the
  public repo. The folder placeholder and the schema (`ideal_response.schema.json`)
  are public for buyer transparency; the actual canonical responses are kept
  in private storage and released only to commercial SFT-dataset buyers.

### Public / commercial split

The repository hosts two tiers of content side by side. The **public tier**
is what gets pushed to GitHub and powers the leaderboard. The **commercial
tier** is the SFT-quality material that is sold to labs as a training
dataset and never leaves the maintainers' machines.

| Field / file | Tier | Where it lives | In public repo? |
|---|---|---|---|
| `criterion_scores.*.score` and `.justification` | public | `scoring/v1.0/**/*.json` | yes |
| `criterion_scores.*.justification_long` | commercial (PREMIUM) | same JSON, optional field | **no — stripped on export** |
| `ideal_responses/v1.0/*.json` (file contents) | commercial (PREMIUM) | local only | **no — gitignored** |
| `ideal_response.schema.json` | public | `system/schemas/v1.0/` | yes |

Before publishing, run the safety gate:

```bash
python scripts/check_public_safety.py
```

It walks `scoring/v1.0/` and `ideal_responses/v1.0/` and fails (exit 1)
if any PREMIUM field or file is present. To produce a sanitized mirror in
one shot (useful for tarballs or for syncing to a separate public worktree):

```bash
python scripts/check_public_safety.py --export public_export/
```

This writes `public_export/scoring/v1.0/**/*.json` with every
`justification_long` removed, and omits `ideal_responses/` entirely.

> Most of this repository is plain Markdown / JSON / YAML and requires no
> local installation to read or contribute. To run the validators or the
> evaluation pipeline locally, see [`scripts/README.md`](scripts/README.md)
> (Python 3.10+, virtual environment, dependencies).

---

## Versioning

The benchmark is published in numbered versions. Each version **does not replace** the previous one: v1.0 remains in force for historical comparison when v2.0 is released.

| Version | Total cases | Public | Private | Status |
|---|---|---|---|---|
| v1.0 | 30 (5 families × 6) | 30 | 0 | *under construction* |
| v2.0 | 80 (8 families × 10) | 40 | 40 | planned |
| v3.0 | 300 (15 families × 20) | 60 | 240 | planned |

**Versioning rules**:

- The folders `/cases/v1.0/`, `/cases/v2.0/` coexist in the repo.
- Git tags (`v1.0.0`, `v1.1.0`) are used only for frozen releases.
- An evaluated response is bound to the benchmark version via the `benchmark_version` field in the JSON. This version implicitly binds the taxonomy, rubric, prompt and schema (principle of "single package per version").

### Scope explicitly deferred to v2.0

To keep v1.0 shippable, the following design decisions are intentionally postponed. Every artifact affected by them carries an explicit note:

| Deferred capability | v1.0 behaviour | v2.0 plan |
|---|---|---|
| **Weighted / ranked main hypotheses** (partial credit) | All entries in `accepted_main_hypotheses` are treated as strictly equivalent (no weights). | Each entry may carry a `weight` in `[0, 1]` so the reviewer can award partial credit for a technically adjacent but non-primary diagnosis. |
| **Reviewer registry binding** | `gold_author_id` and `gold_reviewer_id` in `gold.schema.json` accept any non-empty string. | These fields are bound to a central reviewer registry (`subjects/reviewers.yaml` or equivalent), enabling traceable inter-reviewer κ statistics. |
| **Per-field length limits** in response schema | Only `minLength: 1` is enforced. No maximums. | Maximums tuned empirically from v1.0 run data (95th percentile per field). |
| **Digital certification seal** (`emit_seal.py`) | Scoring produces a leaderboard row only. | Seal issuance pipeline activates (`scripts/emit_seal.py`, `docs/seal_reglamento.md`). |

---

## How to submit a model for evaluation

> Summary flow. Detailed guide in [`docs/submission_guide.md`](docs/submission_guide.md) *(pending)*.
>
> **Operational note**: the flow described below is the target mechanic. End-to-end execution activates with the publication of v1.0; steps marked *(pending)* are not yet enabled.

1. **Register your model** by adding an entry in [`subjects/registry.yaml`](subjects/registry.yaml) via pull request *(PR mechanism pending to be enabled)*. The entry must validate against [`system/schemas/v1.0/registry.schema.json`](system/schemas/v1.0/registry.schema.json) and provide a unique `subject_id`, the `kind` of subject (`llm`, `expert_system`, `human_baseline`, or `committee`), the `provider`, and at least one `version` with its `subject_version`, `registered_at` date, and `access_type`.
2. **Provide API credentials** (or weights, if it is a local model) through a secure channel outside the repo *(secure channel pending to be enabled)*.
3. **BluMind runs the evaluation** against the cases of the requested version *(execution capability pending to be enabled)*.
4. **The committee scores** the responses (2 independent reviewers; third reviewer if there is disagreement) *(committee being formed)*.
5. **You receive a private report** with your full metrics, including breakdown by failure family, ECE by confidence quantile, and comparison against other models *(report format to be defined)*.
6. **The aggregated result is published** on the leaderboard if agreed in the evaluation contract *(evaluation contract pending)*.

**Cost**: the v1.0 evaluation (30 cases) is **free during the foundational phase** (2026) for the first 10 models *(program pending activation)*. Starting from v2.0, the paid service model activates.

---

## How to join as an expert reviewer

> **Operational note**: process in the design phase. The formal opening of recruitment will be announced together with the publication of v1.0.

BluMind selects reviewers with demonstrable experience in water treatment plant operation (minimum 5 years) or in membrane / process R&D. v1.0 specifically requires experience in reverse-osmosis desalination; future versions will open calls for reviewers in other sub-sectors (potabilization, wastewater treatment, water reuse, industrial water). The target process:

1. CV submission to `revisores@blumind.es` *(inbox pending activation)*.
2. Technical interview with a committee member *(committee being formed)*.
3. Calibration test on 3 pilot cases *(pilot cases pending preparation)*.
4. Onboarding via the reviewer guide ([`docs/reviewer_guide.md`](docs/reviewer_guide.md) *(pending)*).

Reviewers sign an NDA and an anonymity agreement *(templates pending)*. Their name never appears publicly; only their anonymized `reviewer_id` (`R01`, `R02`…).

---

## How to contribute

**What we accept via pull request:**

- Typographical or editorial corrections in public documentation.
- Improvements to evaluation scripts (validation, metrics, output format).
- Proposals for new cases (they will be reviewed by the committee before being accepted; template will be published with v1.0).
- Improvements to JSON schemas with technical justification.

**What we do NOT accept via pull request:**

- Modifications to `/golds/` (the public repo does not contain golds).
- Edits to existing files in `/responses/` or `/scoring/` (they are append-only by design — CI blocks it) *(CI rule pending implementation)*.
- Manual edits to `/results/` (it is regenerated from scripts).
- Proposals to modify the generic rubric (discussed in the committee, not in the repo).

---

## Licensing

This repository uses a **mixed license** by content type. Short summary:

- **Python scripts** (`/scripts/`): MIT. Free use, including commercial.
- **Rubric, taxonomy, schemas, documentation, public cases**: Creative Commons BY-NC-SA 4.0. May be used and redistributed with attribution, **non-commercially**, with derivative work under the same license.
- **Responses and scoring** (`/responses/`, `/scoring/`): CC BY-NC-SA 4.0 with an additional attribution clause to the evaluated model.
- **Golds, private cases, "BluMind Certified" seal**: property of BluMind Technologies SL, all rights reserved.
- **Word mark `BluMind` and associated logo**: registered at OEPM under the founder and licensed to BluMind Technologies SL. Use by third parties requires written authorization.

The `LICENSE` file is authored in Spanish as the legally canonical version (Spanish jurisdiction). See [`LICENSE`](LICENSE) for the full text and exact scope of each part.

---

## How to cite

If you use BluMind Benchmark in academic work, technical reports or public comparisons, please cite as:

```bibtex
@misc{blumind_benchmark_2026,
  title        = {BluMind Benchmark: Evaluation of LLMs in Water Plant Operations},
  author       = {{BluMind Technologies SL}},
  year         = {2026},
  howpublished = {\url{https://benchmark.blumind.es}},
  version      = {1.0.0},
  note         = {Foundational version — 5 families, 30 public cases}
}
```

In prose: *"BluMind Benchmark v1.0 (BluMind Technologies SL, 2026)"*.

---

## Contact

- General: `hola@blumind.es` *(pending)*
- Model evaluation: `benchmark@blumind.es` *(pending)*
- Reviewers and committee: `revisores@blumind.es` *(pending)*
- Press and institutional: `institucional@blumind.es` *(pending)*

---

## Project status

**Current version**: v1.0 under construction — 5 families × 6 cases planned (details in [`docs/metodologia.md`](docs/metodologia.md) *(pending)*).
**Next milestone**: release v1.0 with a public leaderboard populated with the main frontier LLMs evaluated.
**Version history**: see [`CHANGELOG.md`](CHANGELOG.md) *(pending)*.

This benchmark is a living product. The rubric version, the case set and the methodology will be refined as the committee accumulates operational evidence. Each version is frozen in its folder and is not overwritten when the next one is published.
