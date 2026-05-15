# Submission Guide — BluMind Benchmark v1.0

This document is the operational guide for organisations wishing to submit an
AI model or system to the BluMind Benchmark. It covers eligibility,
submission requirements, credential handling, pricing, timeline, scoring,
results, re-evaluation, appeals, withdrawal, and contact. For the underlying
evaluation methodology, see [`methodology.md`](methodology.md). For version
history, see [`../CHANGELOG.md`](../CHANGELOG.md).

---

## Overview

This guide is intended for organisations that want to submit an AI model
to the BluMind Benchmark. Typical readers are model providers, fine-tune
developers, integrators exposing a private endpoint, and academic groups
with a deployable model. It is not intended as marketing material; it is
the operational reference that BluMind and submitters use to run an
evaluation end-to-end.

A successful submission produces a single, append-only row on the public
[leaderboard](../results/leaderboard.md), under a pinned `subject_version`
identifier and the associated metrics described in
[`methodology.md`](methodology.md). Submitters may additionally request a
private report (Standard or Premium) as a paid service. Submissions whose
use case falls outside the v1.0 public leaderboard are handled as **custom
evaluations** under a separate engagement.

The high-level flow is:

1. **Submission** — submitter sends a PGP-encrypted email to
   `submissions@blumind.es` with the proposed `subjects/registry.yaml`
   entry, credentials, technical and administrative contacts, and an
   explicit acceptance of these terms.
2. **Validation** — BluMind verifies completeness, eligibility, technical
   access, and benchmark fit. The submission becomes "valid" at this
   point and the evaluation timeline starts.
3. **Evaluation** — the BluMind Technical Committee runs the response
   generation and scoring pipeline under the protocol defined in
   [`methodology.md`](methodology.md).
4. **Result delivery** — the submitter is notified of the outcome, the
   public leaderboard is updated, and, where applicable, a private report
   is delivered.
5. **Post-result mechanisms** — re-evaluation of a new `subject_version`,
   withdrawal, or appeal of a specific result, as described in the
   corresponding sections of this document.

Anything not explicitly described in this document or in
[`methodology.md`](methodology.md) is not part of the BluMind v1.0
contract.

---

## Eligibility and scope

BluMind v1.0 evaluates the **diagnostic and reasoning capability of AI
models** applied to the operation of reverse-osmosis (RO) desalination
plants. The scope, case taxonomy, and rubric are defined in
[`methodology.md`](methodology.md). The list of failure families,
sampling policies, and supported response contract are normative; anything
outside them is, by definition, out of scope for v1.0.

### Who may submit

Any organisation that owns or operates an AI model meeting the eligibility
rules below may submit it for evaluation:

- Frontier-model providers (OpenAI, Anthropic, Google, Meta, Mistral,
  DeepSeek, Qwen, etc.) and their resellers.
- Fine-tune developers exposing their model through a private API or a
  `hosted_endpoint`.
- Research teams and academic groups with a deployable model that satisfies
  the response contract.

Submitters are expected to act in good faith: not training or fine-tuning
on benchmark cases, not coordinating with reviewers, not attempting to
identify reviewers, and not gaming the per-year quota described in
[Re-evaluation Policy](#re-evaluation-policy).

### Accepted subject kinds in v1.0

In v1.0, the public leaderboard accepts only **`kind: llm`** — a single
language model invoked with a single prompt template, with no
retrieval-augmented generation, no tool use, no agent loops, no judge or
re-ranker, and no automatic retries beyond those described in the
methodology. The submitted system must produce a single response per case
that conforms to `system/schemas/v1.0/response.schema.json`.

`kind: human_baseline` and `kind: committee` are reserved for entries
operated and supervised directly by BluMind, in order to preserve the
integrity and comparability of the human reference points on the
leaderboard. They are not freely submittable by third parties in v1.0.

`kind: system` (multi-step pipelines, RAG wrappers, agentic systems,
N8N-style flows, model-plus-tool combinations) and any other compound
configuration are **out of scope** for the v1.0 public leaderboard. The
schema, disclosure requirements, and evaluation contract for compound
systems will be defined in a future benchmark version with a separate
track.

### Out of scope for v1.0

Out of the v1.0 leaderboard, regardless of the submitter:

- Sub-sectors of the water industry other than RO desalination (potable
  water treatment, wastewater, water reuse, ultrafiltration, MBR, EDR,
  industrial water, etc.). These are part of BluMind's long-term scope but
  are not addressed by the v1.0 case set.
- Failure families outside the five v1.0 families (`OXID`, `SCAL`, `FOUL`,
  `MECH`, `NOWE`).
- Sampling modes other than `classic` and `reasoning`.
- Submissions whose system cannot emit a response conforming to
  `response.schema.json`.

### Custom evaluations

Submitters with use cases that fall outside the v1.0 public leaderboard —
for example, evaluating a multi-agent system, a RAG pipeline over private
documentation, a human baseline for a specific utility, evaluation
restricted to a single failure family, or evaluation against a private case
set — may request a **custom evaluation** as a paid service.

Custom evaluations are scoped, priced, and contracted on a per-engagement
basis. They are **not published on the public leaderboard** and do not
count towards the per-year quota of public-leaderboard submissions. Results
are delivered as a private report under the terms of the agreed
engagement. Custom evaluations are subject to operational capacity and
benchmark fit, as described in [Pricing](#pricing).

---

## Submission requirements

A submission is initiated by sending a single email to
`submissions@blumind.es`, encrypted with BluMind's public PGP key. BluMind
is the party that commits new entries to `subjects/registry.yaml`; submitters
do not open pull requests to the registry directly during the foundational
phase.

### Required contents of the submission email

1. **Proposed registry entry**, in YAML, conforming to
   `system/schemas/v1.0/registry.schema.json`. Minimum fields:
   - `subject_id` — stable identifier for the model or system family.
   - `kind` — in v1.0 this must be `llm` (see
     [Eligibility and scope](#eligibility-and-scope)).
   - `provider` — organisation responsible for the submitted system.
   - `versions[].subject_version` — immutable snapshot identifier (for
     example, the provider-pinned model id).
   - `versions[].registered_at` — ISO-8601 date.
   - `versions[].access_type` — see "Accepted access types" below.
   - `versions[].sampling_policy` — see "Sampling policy declaration" below.

2. **Credentials**, delivered in the same encrypted email or in a follow-up
   encrypted message, following the rules in
   [Credential Submission](#credential-submission).

3. **Contacts**:
   - A **technical contact**, responsible for credential rotation,
     endpoint availability, and technical questions during the evaluation.
   - An **administrative contact**, responsible for terms acceptance,
     pricing communications, results delivery, and any appeals.
   Both contacts must use an email address belonging to the submitting
   organisation's domain.

4. **Explicit acceptance of the operative terms**, included verbatim in the
   submission email:

   > On behalf of `<Organisation>`, I confirm that I have read and accept
   > the BluMind Submission Guide and Evaluation Methodology (versions
   > linked in this email) as the operative terms for the evaluation of
   > `subject_id = <X>`, `subject_version = <Y>`.

   The links must point to the specific commit or tag of
   `docs/submission_guide.md` and `docs/methodology.md` in force at the
   moment of acceptance. Acceptance by email is sufficient during the
   foundational phase; paid services may require a separate written
   agreement.

A submission is considered **valid** only when all four elements have been
received and verified by BluMind. The 10-working-day target described in
[Evaluation timeline](#evaluation-timeline) starts from the validation
timestamp, not from the date the email was sent.

### Accepted access types (v1.0)

In v1.0, `versions[].access_type` must be one of:

- **`api`** — a public or private API of the model provider, reachable with
  the credentials supplied by the submitter. This is the default path for
  commercial frontier models.
- **`hosted_endpoint`** — a private HTTP endpoint maintained by the
  submitter for the duration of the evaluation, with an OpenAI- or
  Anthropic-compatible interface. Suitable for in-house fine-tunes that the
  submitter does not want to expose by sharing weights.

Submission of **local model weights** (`local_weights`) is **not accepted**
in v1.0. This restriction may be relaxed in a future benchmark version once
BluMind provides reproducible inference infrastructure and a corresponding
data-handling agreement.

### Sampling policy declaration

Each `versions[]` entry in the registry declares **one and only one**
`sampling_policy`, either `classic` or `reasoning`, as defined in
[`methodology.md`](methodology.md).

If a submitter wishes to evaluate the same underlying snapshot in both
sampling modes, this must be done as **two distinct `subject_version`
entries** — for example, `gpt-5-2025-08-07-classic` and
`gpt-5-2025-08-07-reasoning`. Each entry produces an independent row in the
public leaderboard and counts as a separate submission for the purposes of
the per-year quota described in
[Re-evaluation Policy](#re-evaluation-policy).

---

## Credential Submission

API keys and other credentials must never be sent in plain text.

During the foundational phase, credentials should be submitted by encrypted
email to `submissions@blumind.es` using BluMind's public PGP key, published in
this repository and on BluMind's official website.

Participants should provide evaluation-specific credentials with the minimum
required permissions and appropriate usage or spending limits.

Once received, credentials are imported into BluMind's internal credential
vault and are accessible only to authorized personnel involved in the
evaluation process.

Credentials are retained only for as long as required to complete the
evaluation, technical verification, and any applicable review period. Unless
otherwise agreed, credentials are deleted within 30 days after the evaluation
is completed or the result is published.

Participants are strongly encouraged to rotate or revoke submitted credentials
after the evaluation has been completed.

BluMind will not store credentials in source code, public repositories,
issue trackers, logs, or unencrypted documents.

---

## Pricing

During the foundational phase, BluMind will waive the evaluation fee for
accepted submissions that meet the validation requirements.

A submission is considered valid once all required metadata, credentials, and
technical access requirements have been received and verified.

The foundational phase will remain open until 31 December 2026. Submissions
whose validity is confirmed on or before that date are evaluated under the
foundational-phase terms regardless of the date the evaluation is completed.

After this date, new evaluations and re-evaluations may be subject to
BluMind's commercial pricing terms.

Detailed private reports, custom analyses, expedited evaluations, and
requested re-evaluations may be offered as paid services during or after
the foundational phase.

BluMind reserves the right to decline or defer submissions that fall outside
the benchmark's published scope, that do not meet technical requirements, or
that exceed available operational capacity.

---

## Evaluation timeline

BluMind targets a turnaround of **10 working days** from the moment a
submission is confirmed valid and technical access has been verified to the
completion of the evaluation process.

This is a target, not a contractual SLA: actual timing may depend on reviewer
availability, the number of concurrent submissions, technical issues, and the
complexity of the submitted system.

Submitters receive:
- A confirmation when the submission is validated, normally within 2 working days.
- An expected completion date as part of that confirmation.
- A notification when the evaluation is completed and, where applicable, when the result is published on the public leaderboard.

Expedited evaluations with shorter turnaround times may be offered as a paid service.

---

## Scoring by the BluMind Technical Committee

Every response is scored by the **BluMind Technical Committee** — a body of
senior practitioners and researchers in the water treatment sector. Members
of the committee are listed publicly on
[https://benchmark.blumind.es/committee](https://benchmark.blumind.es/committee)
and include the BluMind founder plus invited experts under formal collaboration
agreements.

For each response:

- The response is scored independently by **two committee members**, drawn
  from the active reviewer pool.
- Reviewers are not informed of the `subject_id` or `subject_version` at the
  moment of scoring; the identity of the model is revealed to them only
  after the per-criterion scores have been committed.
- In the rare case of unresolved disagreement, the response is escalated to
  the full committee for collective resolution.

Within scoring files, individual reviewers are identified only by
`reviewer_id` (`R01`, `R02`, …). The mapping from `reviewer_id` to committee
member is maintained in a private registry kept outside this repository.
This anonymity protects individual reviewers from external pressure and
enables the committee to act as a single institutional authority — the
authoritative entity behind every BluMind score is the committee, not any
single reviewer.

Submitters do not select which committee members score their submission,
and the committee composition for a given evaluation is not communicated
to the submitter.

---

## Public leaderboard

The public leaderboard is published in
[`../results/leaderboard.md`](../results/leaderboard.md) and is generated
deterministically by `scripts/build_leaderboard.py` from
`results/metrics_per_subject.csv`. The leaderboard is the canonical public
record of every BluMind v1.0 evaluation.

### One row per `subject_version`

Each row corresponds to a unique `(subject_id, subject_version)` pair and
is append-only. The set of columns published in v1.0 includes, at minimum:

- `subject` — `subject_id` and `subject_version`.
- `provider` — organisation responsible for the submitted system.
- `sampling_policy` — `classic` or `reasoning`.
- Per-case outcomes — counts of `pass`, `conditional_pass`, and `fail`.
- Critical-fail count — number of cases triggering the safety gate
  defined in [`methodology.md`](methodology.md).
- Aggregated metrics — mean clipped score, Brier score, ECE, and
  `Q_final`.
- `status` — `Eligible` or `Disqualified` based on the safety gate.

The exact column set may evolve in future benchmark versions; changes are
recorded in [`../CHANGELOG.md`](../CHANGELOG.md).

### Publication rules

During the **foundational phase**, every validated submission that
completes evaluation is published on the public leaderboard, regardless
of outcome. Submitting a model during the foundational phase implies
consent to public publication of the resulting row, including a
`Disqualified` status if the safety gate is triggered. There is no
opt-out from publication for foundational-phase submissions.

After the foundational phase, BluMind may offer **private evaluation** as
a paid product, in which the evaluation is performed and the submitter
receives a private report, but no row is added to the public leaderboard.
Private evaluation is contracted as a distinct service and is not part
of the public-leaderboard pipeline.

### Annotations and lifecycle

Public leaderboard rows are not silently overwritten. When the state of a
row changes after publication, BluMind annotates the row using one of
three labels, with a short note linking to the underlying justification:

- **`corrected`** — the evaluation has been re-run because of a material
  error attributable to BluMind, or because an appeal was upheld
  (see [Appeals](#appeals)). The original metrics are replaced with the
  corrected ones; the annotation remains visible.
- **`withdrawn`** — the submitter has requested withdrawal of the entry
  after publication (see [Withdrawal and data retention](#withdrawal-and-data-retention)).
  The row remains visible as historical record, marked as withdrawn; its
  metrics are no longer used in active comparisons.
- **`invalidated`** — BluMind has determined that the evaluation cannot
  be relied upon, typically because of documented training-data
  contamination, breach of the good-faith clause described in
  [Eligibility and scope](#eligibility-and-scope), or fraud detected
  after publication. Invalidation is decided by the BluMind Technical
  Committee and is final.

All annotations are append-only. Once applied, a `corrected`,
`withdrawn`, or `invalidated` annotation cannot be removed; further
changes only add new annotations on top, never erase prior ones. This
preserves a full public audit trail of every row's history.

---

## Private Reports

BluMind may offer private evaluation reports as a paid service during or after
the foundational phase. Private reports are intended to help submitters
understand model performance, identify failure modes, and prioritize
improvements.

Private reports do not include full gold answers, complete benchmark solutions,
or detailed scoring artifacts from other submitted systems.

### Standard Private Report

The Standard Private Report may include:

- Overall benchmark score and public leaderboard context.
- Per-case breakdown for the submitted system.
- Per-family performance breakdown.
- Short criterion-level scoring notes.
- Critical-fail summary, where applicable.
- Basic calibration metrics, such as Brier score and ECE, where available.
- Aggregated comparison against current top-performing systems.
- A PDF report.
- A ZIP file containing machine-readable scoring artifacts and model responses
  for the submitted system.

### Premium Expert Report

The Premium Expert Report may include everything in the Standard Private Report,
plus:

- Detailed reviewer justifications, where appropriate and subject to benchmark
  integrity constraints.
- Full failure-mode profile for the submitted system.
- Specific mitigation recommendations, such as prompting changes, fine-tuning
  priorities, guardrail improvements, or additional evaluation needs.
- A signed or sealed PDF report, when available.
- One remote Q&A session of up to 60 minutes with BluMind or its evaluation committee.

Private reports are typically delivered within 5 working days of evaluation
completion. This is a target, not a contractual SLA.

Reports are delivered in English by default. Spanish may be available on request.

### Restrictions

Private reports are limited to the submitted system. BluMind does not disclose
full gold answers, hidden benchmark materials, detailed per-case scoring for
other systems, or private reviewer justifications belonging to other submitters.

---

## Re-evaluation Policy

A `subject_id` identifies a submitted model or system family. A
`subject_version` identifies a specific immutable snapshot of that system.

Each `subject_version` declared in `subjects/registry.yaml` is evaluated
**only once**. The pinned version, for example `gpt-5-2025-08-07`, is the
atomic unit of the leaderboard: its score is append-only.

To re-evaluate a model or system, the submitter must register a **new
`subject_version`** — typically a new snapshot, fine-tune iteration, or
prompt-pipeline revision — and submit it as a fresh evaluation.

The previous `subject_version` remains in the leaderboard as historical record
and is not overwritten. BluMind may mark entries as withdrawn, corrected, or
invalidated where necessary, but does not silently overwrite historical scores.

To prevent gaming and protect operational capacity:

- A given `subject_id` may submit **up to 4 distinct `subject_version` entries
  per calendar year** during the foundational phase. Higher volumes may be
  arranged as part of a paid plan.
- Re-evaluation of the **same** `subject_version` is not accepted, except in
  the case of a documented technical error that materially affected the
  evaluation. If the error is attributable to BluMind, the original evaluation
  is re-run at no cost and the published result is corrected.

Disqualification through a critical-fail safety gate is applied per
`subject_version`, not per `subject_id`. A new `subject_version` starts with a
clean evaluation record.

---

## Appeals

A submitter may appeal an evaluation result if they believe one of the
following has occurred:

- A **material error** in the evaluation, such as the wrong `subject_version`
  being evaluated, a material input or submitted output being demonstrably
  omitted from the evaluation record, or a computational error in the
  aggregated metrics.
- A **procedural error**, such as the published methodology not being followed
  in a way that materially affected the result.
- A substantiated concern of **reviewer bias or undisclosed conflict of
  interest** affecting the scoring.

The following are **not** grounds for appeal:

- Subjective disagreement with a per-criterion score where the rubric was
  correctly applied.
- Retrospective reinterpretation of the rubric, taxonomy, or gold references
  in force at the time of the evaluation.
- Changes in the submitter's own model or system after the evaluation has
  been completed. These are handled through the re-evaluation policy.

### Procedure

- Appeals must be submitted in writing within **14 calendar days** of result
  delivery, citing the specific evaluation, the claimed error, and the
  evidence supporting it.
- The appeal is reviewed by the BluMind Technical Committee. The reviewers
  involved in the original scoring **do not participate** in the appeal
  review.
- The committee issues a written decision within **20 working days** of
  receiving a complete appeal.
- If the appeal is upheld, the original evaluation is corrected and the
  leaderboard entry is updated with a `corrected` annotation. If the
  underlying error is attributable to BluMind, the correction is made at
  no cost to the submitter.
- The committee's decision on an appeal is **final**. There is no second
  instance.

---

## Withdrawal and Data Retention

A submitter may withdraw a submission before scoring has started. In that case,
the submission is closed without publication on the public leaderboard.

Once a result has been published on the public leaderboard, the corresponding
leaderboard entry is not deleted. If a submitter requests withdrawal after
publication, BluMind may mark the entry as `withdrawn` while preserving the
historical record of the evaluation.

During the foundational phase, post-publication withdrawal requests are handled
without charge. After the foundational phase, withdrawal handling may be subject
to BluMind's commercial terms where additional operational, administrative, or
legal review is required.

BluMind retains evaluation artifacts, including model responses, scoring
records, reviewer notes, and leaderboard metadata, as needed to preserve the
integrity, reproducibility, auditability, and historical continuity of the
benchmark.

Credential material, including API keys and access tokens, is not treated as a
benchmark artifact. Credentials are retained only for as long as required to
complete the evaluation, technical verification, and any applicable review
period, and are deleted according to the credential retention policy.

Commercial and administrative records, including submitter contact details,
contractual records, invoices, paid report records, and related business
correspondence, may be retained for up to 6 years after the submission is closed
or the relevant commercial relationship ends, unless a longer retention period
is required by law.

Private reports and related commercial deliverables are retained only as needed
for contractual, audit, support, or dispute-resolution purposes, and are not
published as part of the public leaderboard.

BluMind does not delete, overwrite, or silently modify historical leaderboard
records. Where appropriate, entries may be marked as `corrected`, `withdrawn`,
or `invalidated`.

---

## Contact

The BluMind Benchmark is maintained by **Álvaro Díaz del Río Redondo**,
Founder of BluMind, on behalf of the BluMind project. The founder is the
public point of accountability for the benchmark and oversees the contractual
and accountability aspects of each evaluation.

Contact channels:

- Submissions and credential delivery: `submissions@blumind.es`
- Appeals and matters concerning the BluMind Technical Committee:
  `committee@blumind.es`
- Pricing, custom evaluations, and general inquiries: `info@blumind.es`
- Direct founder contact: `alvaro@blumind.es`

All credential material and any other confidential content must be sent
exclusively to `submissions@blumind.es`, encrypted with the BluMind public
PGP key.

The BluMind public PGP key is published in this repository at
[`../system/keys/blumind-submissions.asc`](../system/keys/blumind-submissions.asc)
and on BluMind's official website. Before sending any credential material,
verify that the key fingerprint matches:

```
42E1 6A9D FD54 0917 4B3B  AA2A F329 316C 1392 A8F2
```

Instructions for importing and verifying the key are provided in
[`../system/keys/README.md`](../system/keys/README.md).

Unencrypted credential material received at any other address is considered
invalid and will be discarded. The submitter will be asked to re-send the
credentials through the secure channel.
