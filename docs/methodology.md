# Methodology — BluMind Benchmark v1.0

> Entry-point document for anyone (lab, reviewer, journalist, jurado) who wants
> to understand **how** BluMind measures what it claims to measure.

BluMind Benchmark evaluates the ability of AI models (LLMs and expert systems)
to diagnose and reason about real operational problems in the water treatment
sector. v1.0 is acotated to reverse-osmosis (RO) desalination plants; future
versions will progressively cover the rest of the sector (potabilization,
wastewater, reuse, industrial water — see [`../README.md`](../README.md) § Scope).

This document is a **map**, not the source of truth. The authoritative
artifacts for each section are linked inline. If this document and an
authoritative file disagree, the authoritative file wins; please open an issue.

---

## 1. What we measure

Every benchmark case presents the subject with:

- A real operational situation (symptoms, sensor readings, recent history) from
  an anonymised plant report.
- An explicit JSON output contract.

The subject produces a single-shot JSON response with seven scored fields plus
six traceability fields. A human expert reviewer scores the response 0–12
against a private gold standard, augmented with up to three case-specific
automatic-fail rules.

We **do not** measure:

- Open-ended chat quality, tone or empathy.
- Step-by-step chain-of-thought (only the final structured output is scored).
- Tool use, retrieval, multi-turn dialogue or agentic behaviour.

These are deliberate v1.0 boundaries. v2.0 may add a tool-augmented track.

---

## 2. Case taxonomy

Cases are identified by `RO-<FAMILY>-<NNN>`. v1.0 ships **5 failure families,
31 cases**:

| Code | Family | Why it is in the benchmark |
|---|---|---|
| `OXID` | Oxidative damage | Highest cost per diagnostic error — irreversible. |
| `SCAL` | Inorganic scaling | The most frequent in real plants. |
| `FOUL` | Organic / biological fouling | The one most confused with other causes. |
| `MECH` | Mechanical damage / integrity | Discriminates against those who confuse fouling with mechanical failure. |
| `NOWE` | No-wetting / abnormal startup | Edge case — separates experts from generalists. |

Cases come in four **types** (`Closed`, `Semi-closed`, `Open`, `Ambiguous`)
that modulate how the rubric is applied — see § 4.

**Authoritative source**: [`../system/families/v1.0/taxonomy.md`](../system/families/v1.0/taxonomy.md).

---

## 3. Response contract

The subject must emit a JSON object validated against [`../system/schemas/v1.0/response.schema.json`](../system/schemas/v1.0/response.schema.json).

| Field | Purpose | Notes |
|---|---|---|
| `case_id`, `benchmark_version`, `subject_id`, `subject_version`, `run_id`, `timestamp_utc`, `served_model` | Traceability metadata | Not scored. |
| `track` | Sampling mode annotation (`classic` / `reasoning`) | Copied from the subject's registry entry. |
| `main_hypothesis` | Most likely root cause, single sentence | Scored (rubric criterion 1). |
| `confidence` | Subjective confidence 0–100 | **Not** scored per case. Feeds Brier and ECE longitudinally. |
| `key_signals` | Variables from the case that support the hypothesis | Scored (criterion 2). Inventing signals not present in the case is forbidden. |
| `alternatives` | Plausible rival hypotheses with `why_plausible` / `why_discardable` | Scored (criterion 3). Minimum one. |
| `recommended_action` | Concrete operational action | Scored (criterion 4). |
| `requested_data` | The "trigger" datum that would most reduce uncertainty | Scored (criterion 5). |
| `decision_change_condition` | Threshold under which the recommendation would change | Scored (criterion 6). |

The prompt template the subject receives is [`../system/prompts/v1.0/prompt_template.md`](../system/prompts/v1.0/prompt_template.md). It is identical across subjects and tracks; only sampling parameters vary (§ 6).

**Design rule**: every field requested from the subject has one of three
declared purposes — **per-case rubric**, **longitudinal metric**, or
**operational metadata**. No field without a declared purpose.

---

## 4. Scoring rubric

The rubric scores each response on **six criteria**, each worth 0–2 points
(total 0–12). The classification is then derived from the score plus any
automatic fails:

| Classification | Condition |
|---|---|
| `Pass` | `clipped_score ≥ 10` and no automatic fail |
| `Conditional` | `clipped_score ∈ [7, 9]` and no automatic fail, **or** any recoverable automatic fail |
| `Fail` | `clipped_score < 7`, **or** `clipped_score < gold.rubric_floor`, **or** any **critical** automatic fail |

Where `clipped_score = min(raw_score, gold.rubric_ceiling)`.

**Two crucial concepts**:

- **Automatic fails** — actions whose mere presence overrides the score. They
  come in two flavours:
  - **Critical** — irreversible damage OR no time window for a second
    review layer to catch the error. Forces `Fail` regardless of score.
    Example: *"recommending acid CIP under suspicion of oxidative damage"*.
  - **Recoverable** — wrong order or wrong reasoning, but a senior operator
    can still catch it before execution. Forces `Conditional`. Example:
    *"CIP without prior mechanical integrity check"*.

- **Case-type modulation** — `Open` and `Ambiguous` cases score reasoning
  quality (alternatives, counterfactual conditions) more strictly than
  hypothesis identification. `Closed` cases work the opposite way.

**Authoritative source**: [`../system/rubric/v1.0/generic_rubric.md`](../system/rubric/v1.0/generic_rubric.md) — full criterion table, case-type implications, automatic-fail severity rules, and gold-level overrides (`rubric_floor`, `rubric_ceiling`).

---

## 5. Aggregated metrics

After every (case, subject, run, reviewer) tuple has been classified, the
script `scripts/compute_metrics.py` derives per-subject metrics.

| Metric | What it answers | Range | Better when |
|---|---|---|---|
| `P` — Pass rate | How often does this subject cross the strict bar? | `[0, 1]` | higher |
| `s̄` — Mean clipped score | How strong is the reasoning content on average? | `[0, 12]` | higher |
| `BS` — Brier score | Is the subject's stated confidence calibrated? | `[0, 1]` | lower |
| `ECE` — Expected Calibration Error | Same, with 10 fixed-width bins | `[0, 1]` | lower |
| `Q_final` — Composite quality | The leaderboard ranking column | `[0, 1]` | higher |
| `disqualified` — Safety gate | Triggered if any case had a critical fail | bool | `False` |

`Q_final` is computed as:

```
Q_final = α · P + (1 - α) · (s̄ / 12),   α = 0.5 in v1.0
```

`α` is the **only arbitrary number** in the formula stack and is stored
alongside every historical result for reproducibility.

`Q_final` deliberately **does not** include calibration. Mixing Brier or ECE
into the composite would let an over-cautious subject (always declaring 50 %
confidence) outrank a competent but slightly overconfident one. Calibration is
reported alongside `Q_final` so reviewers can read both — but it does not enter
the ranking.

**Safety gate**: any subject with ≥ 1 critical automatic fail is marked
`Disqualified`. Its metrics are still computed and published (transparency >
silent suppression), but the leaderboard row is flagged. Disqualification is
per `subject_version`, not per `subject_id` — a new pinned snapshot starts
with a clean record.

**Authoritative source**: [`../system/rubric/v1.0/aggregated_metrics.md`](../system/rubric/v1.0/aggregated_metrics.md) — full formulas, derivation order, sample-size caveats, and rationale for design choices (soft Brier, 10 fixed-width ECE bins, 50/50 composite weighting).

---

## 6. Sampling policy

v1.0 ranks every subject in a **single public leaderboard**. The sampling
mode is annotated per row, not partitioned — in line with mainstream
evaluation practice (HELM, MMLU-Pro, GPQA, Artificial Analysis).

| Mode | Sent to provider | Omitted | Track annotation |
|---|---|---|---|
| `classic` (original v1.0 contract) | `temperature=0` | reasoning controls | `track: "classic"` |
| `reasoning` (frontier reasoning models) | `reasoning_effort` only | `temperature`, `top_p`, `top_k` | `track: "reasoning"` |

The `reasoning` mode exists because some 2026-vintage frontier models
(GPT-5.5, Claude Opus 4.7, …) reject `temperature` outright. Forcing a
classic contract on them returns API errors. The runner therefore accepts
exactly **one** portable knob (`reasoning_effort`) which LiteLLM translates
per provider, and pins everything else to provider defaults.

Each subject's mode is declared in [`../subjects/registry.yaml`](../subjects/registry.yaml) (`sampling_policy.kind`), validated by the registry schema, and copied verbatim into every response under the `track` field. The leaderboard renders it as an emoji column (🧠 reasoning / classic).

The reasoning mode is acknowledged as **inherently less bit-perfect** than
classic. The benchmark accepts this trade-off to evaluate models that simply
cannot run on the classic contract.

**Authoritative source**: [`run_evaluation_design.md`](run_evaluation_design.md) § 6 (cost/token telemetry) and § 7 (sampling policy rationale).

---

## 7. Reproducibility & provenance

Every benchmark version is treated as a **single immutable package**:

- The folders `cases/v1.0/`, `system/rubric/v1.0/`, `system/schemas/v1.0/`,
  `system/families/v1.0/`, `system/prompts/v1.0/` co-exist with future
  versions; they are never overwritten.
- An evaluated response is bound to the benchmark version via the mandatory
  `benchmark_version` field in `response.schema.json`. This implicitly binds
  taxonomy, rubric, prompt and schema versions in force at that moment.
- Git tags (`v1.0.0`, `v1.0.1`) are used only for frozen releases.
- The leaderboard always displays the reference version of the score
  (e.g. *"Pass rate 0.73 [v1.0]"*).
- When a MAJOR version is released, the v1.0 leaderboard is preserved as
  frozen history under `results/history/`.

**Determinism of derived outputs**:

- `compute_metrics.py` emits byte-identical CSVs given identical inputs:
  rows are sorted by `(subject_id, case_id, run_id, reviewer_id)` or
  `(subject_id, family)`.
- `build_leaderboard.py` is deterministic on the same inputs: only the
  `Last update` timestamp varies (derived from the most recent scoring
  file, not from wall-clock time).
- `run_evaluation.py` is **not** deterministic across runs — even with
  `temperature=0`, providers do not guarantee bit-perfect outputs.
  Reproducibility at the response level is therefore a best-effort target;
  reproducibility at the *metric* level is enforced by the append-only
  storage policy (a published row is never recomputed after the fact;
  if the underlying response changes, the run gets a new `run_id`).

**Versioning rules**:

| Bump | Triggers | Score comparability |
|---|---|---|
| MAJOR (`v1.0 → v2.0`) | Rubric changes, scored-field changes | **Not** comparable across majors |
| MINOR (`v1.0 → v1.1`) | New cases / families / documentation | Previous scores remain comparable |
| PATCH (`v1.0.0 → v1.0.1`) | Errata, clarifications | Never affects calculations |

**Authoritative source**: [`../CHANGELOG.md`](../CHANGELOG.md) (version history) and [`run_evaluation_design.md`](run_evaluation_design.md) § *Cross-cutting concerns* (determinism, append-only outputs, traceability fields).

---

## 8. Public / commercial split

BluMind is deliberately **hybrid**. Credibility comes from the public side;
defensible revenue comes from the private side. The split is enforced at the
schema and gate level:

| Tier | What it is | In public repo? |
|---|---|---|
| Public — case statements | Operational situation presented to the subject | yes |
| Public — schemas | All five JSON Schemas | yes |
| Public — responses | Subject outputs | yes |
| Public — scoring (telegraphic) | `score` + short `justification` per criterion | yes |
| Commercial — scoring (rich prose) | Optional `justification_long` per criterion | **no — stripped on export** |
| Commercial — ideal responses | Canonical expert answers per case | **no — gitignored** |
| Private — golds | Reference root causes & accepted hypotheses | **no — separate private repo** |
| Private — reviewer registry | `reviewer_id` ↔ real-name mapping | **no — outside this repo** |

The fence is implemented by [`../scripts/check_public_safety.py`](../scripts/check_public_safety.py):

- Default mode audits the repo and fails (exit 1) if any PREMIUM field
  or file is present, printing the exact paths.
- `--export DIR/` produces a sanitized mirror with `justification_long`
  stripped and `ideal_responses/` omitted, ready to publish.

Publishing schemas for the premium fields (even though the content is
private) is a deliberate transparency choice: buyers of the commercial
dataset want to know exactly what they will receive.

**Authoritative sources**:
- Schemas: [`../system/schemas/v1.0/evaluation.schema.json`](../system/schemas/v1.0/evaluation.schema.json) (PREMIUM field marked), [`../system/schemas/v1.0/ideal_response.schema.json`](../system/schemas/v1.0/ideal_response.schema.json).
- Gate: [`../scripts/check_public_safety.py`](../scripts/check_public_safety.py).
- Workflow: [`../README.md`](../README.md) § Public / commercial split.

---

## 9. Limitations of v1.0

Documenting limitations honestly is part of the methodology:

| Limitation | Why it is OK for v1.0 | Plan |
|---|---|---|
| **N = 31 cases** | Aligned with comparable bootstrapping benchmarks (HumanEval ≈ 164; GPQA-Diamond ≈ 198). ECE and per-family breakdowns are labelled **indicative**. | v2.0 target: N ≈ 80. v3.0: N ≈ 300. |
| **One reviewer per (case, subject, run)** | Avoids forced consensus in ambiguous cases. Inter-reviewer κ is deferred to v2.0. | v2.0: 2 reviewers + arbiter when divergence. |
| **Reasoning track non-deterministic** | Frontier providers don't guarantee bit-perfect outputs even at `temperature=0`. | v2.0: explore the providers' `seed` parameter when stable. |
| **No tool use / RAG track** | One contract per release. | v2.0: optional tool-augmented track, scored separately. |
| **RO desalination only** | First acotated release. Validates the methodology. | v2.0+: open progressively to potabilization, wastewater, reuse, industrial water. |
| **Reviewer-registry binding not enforced** | `gold_author_id` accepts any non-empty string. | v2.0: bound to a central reviewer registry for traceable κ statistics. |
| **No digital seal / certificate** | Manual leaderboard suffices. | v2.0: `scripts/emit_seal.py` + `docs/seal_reglamento.md`. |

**Authoritative source**: [`../README.md`](../README.md) § *Scope explicitly deferred to v2.0* and [`../CHANGELOG.md`](../CHANGELOG.md).

---

## 10. References

| Topic | File |
|---|---|
| Family taxonomy | [`../system/families/v1.0/taxonomy.md`](../system/families/v1.0/taxonomy.md) |
| Generic rubric | [`../system/rubric/v1.0/generic_rubric.md`](../system/rubric/v1.0/generic_rubric.md) |
| Aggregated metrics | [`../system/rubric/v1.0/aggregated_metrics.md`](../system/rubric/v1.0/aggregated_metrics.md) |
| Prompt template | [`../system/prompts/v1.0/prompt_template.md`](../system/prompts/v1.0/prompt_template.md) |
| Response schema | [`../system/schemas/v1.0/response.schema.json`](../system/schemas/v1.0/response.schema.json) |
| Evaluation schema | [`../system/schemas/v1.0/evaluation.schema.json`](../system/schemas/v1.0/evaluation.schema.json) |
| Gold schema | [`../system/schemas/v1.0/gold.schema.json`](../system/schemas/v1.0/gold.schema.json) |
| Ideal-response schema | [`../system/schemas/v1.0/ideal_response.schema.json`](../system/schemas/v1.0/ideal_response.schema.json) |
| Registry schema | [`../system/schemas/v1.0/registry.schema.json`](../system/schemas/v1.0/registry.schema.json) |
| Runner design notes | [`run_evaluation_design.md`](run_evaluation_design.md) |
| Reviewer guide | [`reviewer_guide.md`](reviewer_guide.md) |
| Results CSVs guide | [`../results/README.md`](../results/README.md) |
| Public-safety gate | [`../scripts/check_public_safety.py`](../scripts/check_public_safety.py) |
| Metrics computation | [`../scripts/compute_metrics.py`](../scripts/compute_metrics.py) |
| Leaderboard generation | [`../scripts/build_leaderboard.py`](../scripts/build_leaderboard.py) |
| Version history | [`../CHANGELOG.md`](../CHANGELOG.md) |

---

## How to cite

If you use BluMind Benchmark in academic work, technical reports or public
comparisons, see [`../README.md`](../README.md) § *Citation* for the BibTeX entry.
