# Design notes — `scripts/run_evaluation.py`

This document records the design decisions taken for the v1.0 evaluation
runner so that, six months from now, the rationale for each choice is
recoverable without reading the source code.

The script's job is narrow: take one or more cases from `cases/v1.0/`,
ask one or more LLMs to solve them under the conditions defined in
`system/prompts/v1.0/prompt_template.md`, and store the responses in a
shape that the rest of the pipeline (scoring, metrics, leaderboard)
can consume.

---

## 1. LLM gateway: LiteLLM

**Chosen**: a single call site through [LiteLLM][litellm] for every
provider.

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| Native SDKs (`openai`, `anthropic`, …) | Maximum control, no third-party intermediary | One adapter per provider; ongoing maintenance when each provider's API drifts |
| Custom thin abstraction over native SDKs | Clean separation of concerns | Same maintenance burden plus our own abstraction to maintain |
| LiteLLM | Unified interface, 100+ providers out of the box, retries built-in, MIT-licensed | Adds one external dependency |

**Rationale**: a benchmark that aspires to evaluate any frontier model
should not pay one engineering tax per provider. LiteLLM is the de-facto
standard for this in 2026 and is used by major evaluation frameworks. We
remain free to swap it out — every call is funnelled through one
function (`call_model`), so a future replacement is local.

**Mapping subjects to LiteLLM model strings**: the script composes the
identifier as `<provider_lower>/<subject_id>` (e.g. `openai/gpt-5`)
using the `provider` field from `subjects/registry.yaml` and a small
mapping table in the script (`PROVIDER_TO_LITELLM_PREFIX`). Operators
can override on the command line with `--litellm-model` for cases where
LiteLLM expects a more specific identifier (date-stamped releases,
staging endpoints, etc.). When a brand-new provider is added to the
registry, the table is extended in one line — no other code changes.

[litellm]: https://github.com/BerriAI/litellm

---

## 2. Secrets management: `.env` file

**Chosen**: a `.env` file at the repository root, loaded automatically
by `python-dotenv` at script startup.

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| Pure environment variables (export in shell) | Zero file footprint | Lost between sessions; tedious in daily use |
| `.env` file | Persistent across sessions; standard for Python projects in 2026 | Must remain ungitted (already enforced) |
| Cloud secrets manager (AWS / GCP / Vault) | Centralised, auditable | Massive overkill for one user with two API keys |

**Rationale**: `.env` is the lowest-friction option that does not leak
secrets into the repo. The `.gitignore` already excludes `.env` and
`.env.*` while explicitly allowing `.env.example`, which is committed
to document required variables.

**Files involved**:

- `.env` — actual keys (gitignored).
- `.env.example` — template with the variable names and links to each
  provider's key-management page (committed).

---

## 3. Execution modes: flexible CLI filters

**Chosen**: combinable filters `--case`, `--family`, `--subject`,
plus `--all` as the explicit guard for unfiltered runs.

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| Only one-at-a-time (`--case X --subject Y`) | Simplest interface | Tedious for 60-run batteries |
| Only full battery | One-command operation | Cannot debug or re-run a single failure |
| Flexible (chosen) | Covers debugging and battery use cases | A few more lines of argparse |

**Rationale**: a benchmark battery exposes errors in cases and subjects
unevenly. The script must support the smoke test (one case × one
subject), the family-level diagnostic (all FOUL cases × one subject),
and the full pass — all in one tool. The `--all` guard prevents
accidental no-filter runs from spending API budget by surprise.

**Out of scope for v1.0**: parallelism. Calls are sequential. With 60
runs at ~10–15 seconds each, the wall-clock cost of a full battery is
~10–15 minutes, which is tolerable. Concurrency may be added later if
N grows or batteries become routine.

---

## 4. Retries: 3 attempts with exponential backoff

**Chosen**: `num_retries=3` delegated to LiteLLM. The exponent is
LiteLLM's default (2 → 4 → 8 seconds between attempts). Configurable
via `--retries N`.

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| No retries | Simplest | Transient 5xx / rate-limit errors leave gaps in the battery |
| 3 retries fixed | Standard | None of consequence |
| Configurable | Slightly more flexible | Adds a flag for negligible benefit; we use the default 99% of the time |

**Rationale**: 3 attempts with backoff resolves >95% of transient
provider failures, matches industry convention, and adds zero code
because LiteLLM ships it. The flag is exposed for completeness but the
default is the expected setting.

**What is NOT retried**: schema validation failures and JSON parse
errors. Those are deterministic outputs from a deterministic call
(`temperature=0`, `top_p=1`). Retrying them is unlikely to change the
outcome and would muddy reproducibility. They go straight to the error
path.

---

## 5. Invalid responses: log and continue

**Chosen**: when a response cannot be parsed as JSON or fails the
schema, the script saves the raw model output and a diagnostic log to
`responses/v1.0/<subject_id>/_errors/`, marks the run as failed, and
proceeds to the next `(case, subject)` pair.

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| Hard-fail the batch on first invalid response | Forces immediate attention | Loses the remaining good runs of a 60-run battery |
| Log and continue (chosen) | Battery completes unattended; failures are auditable | None of consequence |
| Auto-repair (regex extraction, manual JSON cleanup) | Salvages near-misses | **Contaminates the benchmark**: a model that fails to emit clean JSON has, by the prompt's own contract, failed automatic-validation; rescuing it is methodologically wrong |

**Rationale**: the prompt template explicitly classifies "output is not
a single parseable JSON object" as an automatic validation failure. The
runner faithfully encodes that contract. Auto-repair would produce
results that disagree with the published evaluation rules and would be
indefensible under external review.

**Storage layout for failures**:

```
responses/v1.0/<subject_id>/_errors/
  RO-XXXX-NNN__run-YYYY-MM-DD-NNN.txt        ← raw model output
  RO-XXXX-NNN__run-YYYY-MM-DD-NNN.error.log  ← stack-style diagnostic
```

Both files are kept indefinitely (append-only, like successful runs).
This is the audit trail.

---

## Cross-cutting concerns

### Determinism

`temperature=0` and `top_p=1` are hard-coded in `call_model`. They are
not exposed as CLI flags because the prompt template fixes them
explicitly as part of the v1.0 contract, and changing them would
require a benchmark-version bump.

### Traceability fields

The model produces only the seven content fields. The script wraps the
response with:

| Field | Source |
|---|---|
| `case_id` | The `## case_id` section of the case markdown |
| `benchmark_version` | Hard-coded to `v1.0` (this script is v1.0-only) |
| `subject_id` | CLI / registry |
| `subject_version` | `--subject-version` or last entry in registry's `versions` array |
| `run_id` | Auto-generated: `run-YYYY-MM-DD-NNN` (NNN auto-increments) |
| `timestamp_utc` | UTC ISO-8601 with `Z` suffix at the moment of writing |

### Append-only outputs

The script never overwrites an existing response. Each invocation
produces a fresh `run_id`. This protects historical leaderboard data
against accidental mutation and makes `responses/v1.0/` safe to
include in CI integrity checks in future versions.

### Idempotency and reproducibility

Two runs of the same `(case, subject_id, subject_version)` will
typically produce identical content (because of `temperature=0`), but
the `run_id` and `timestamp_utc` differ — so they live as separate
files. Aggregation scripts (planned) will be responsible for choosing
which run to score per `(case, subject)` pair.

---

## What is intentionally NOT in this script

- **Scoring**. The script never computes a score. It only produces
  the artefact (the response JSON) that scorers will later consume.
- **Aggregation across runs**. Picking the canonical run per
  `(case, subject)` is the responsibility of `aggregate_scoring.py`
  (planned).
- **Leaderboard generation**. Same logic — that is `build_leaderboard.py`.
- **Human-baseline capture**. Subjects with `kind=human_baseline` are
  silently skipped: the access path for those is a separate intake
  pipeline (form / CLI / manual) outside this script's scope.
- **Hard budget guards**. The script does not enforce a maximum spend.
  Hard caps belong on the provider side (OpenAI / Anthropic dashboards),
  where they are configured per account and cannot be bypassed by a
  buggy script. The runner only reports cost; it does not gate it.

---

## 6. Per-call cost and token telemetry

**Chosen**: every call captures `prompt_tokens`, `completion_tokens`,
`total_tokens`, USD cost (via `litellm.completion_cost`) and latency in
milliseconds. The values are printed inline next to PASS/FAIL, summed
into a per-batch summary at the end, and persisted to a CSV log under
`logs/batch_logs/<utc-timestamp>.csv` (gitignored).

**Alternatives considered**:

| Option | Pros | Cons |
|---|---|---|
| No telemetry (estimate from provider dashboard) | Zero code, the dashboard is the truth | Estimates only, retroactive, no per-case attribution, no auditability of which run cost what |
| Token logging only | Cheap, no pricing dependency | Cost still requires manual conversion; pricing changes are not surfaced |
| Token + LiteLLM cost (chosen) | Real-time per-call attribution, batch summary, auditable CSV trail, no extra deps | Cost figures may lag dashboard pricing by hours/days when providers change rates |
| Pre-flight token estimation (`tiktoken`) before the call | Forecasts spend before money is committed | Useful for `--all`, overkill for the typical batch; can be added later as a `--estimate-cost` flag |

**Rationale**: a benchmark that publishes leaderboards must publish
operational telemetry too. Knowing exactly what a battery cost in tokens
and USD per `(case, subject)` is a precondition for fairness analysis
("did model X take 3× the output tokens of model Y for the same case?")
and for transparent reporting in the methodology document.

**Defensive behaviour**: every metric is independently optional.

- If the provider does not return `usage` info, token counts are stored
  as empty.
- If LiteLLM has no pricing entry for the model, `cost_usd` is empty
  and a warning is printed in the batch summary; the runs themselves
  succeed.
- Cost-extraction errors never propagate: `extract_call_metrics` is
  wrapped in `try/except` and degrades gracefully.

**Storage**:

- **stdout**: per-call line `... PASS  in=2840 out=1120  cost=$0.0341  → ...`,
  plus a final summary with per-subject breakdown.
- **CSV**: `logs/batch_logs/<YYYY-MM-DDTHH-MM-SSZ>.csv` with columns
  `timestamp_utc, case_id, subject_id, subject_version, run_id, track,
  litellm_model, served_model, prompt_tokens, completion_tokens,
  total_tokens, cost_usd, price_per_input_token_usd,
  price_per_output_token_usd, latency_ms, status, error_type`. Includes
  failed runs (because failures still incur API spend in many cases).
  The unit-pricing columns are read from LiteLLM's `model_cost` table
  at run time and fixed in the log, so the price the benchmark version
  was actually evaluated under remains auditable even after the
  provider changes rates downstream. The `track` and `served_model`
  columns let cost analyses split classic vs reasoning runs (see § 7)
  and audit alias drift after the fact.

The CSV directory is under the gitignored `logs/` tree by design: cost
telemetry is operational data, not benchmark output, and it can reveal
internal API spend that has no business being public. Operators who
want to publish a redacted version (e.g. token counts only, no prices)
can copy specific files into a public location manually.

**Reconciliation**: the batch CSV is for live awareness; the provider
dashboard remains the authoritative source for billing. Differences
under ~5 % are normal and reflect either pricing-table lag in LiteLLM
or rounding. Larger discrepancies indicate either a recent provider
pricing change (update the LiteLLM dependency) or a logging bug.

---

## 7. Sampling policy — per-subject, single leaderboard

**Chosen**: every `kind: llm` entry in `subjects/registry.yaml` **must**
declare a `sampling_policy` block that pins it to one of two sampling
modes. The benchmark publishes a **single leaderboard** with the mode
rendered as an informational annotation column — it does **not** split
the table.

| Mode | What the runner sends | What the runner omits | Annotation emitted to response.json |
|---|---|---|---|
| `classic` (original v1.0 contract) | `temperature=0` | `top_p`, `top_k`, all reasoning controls | `track: "classic"` |
| `reasoning` (frontier reasoning models) | `reasoning_effort` (only if declared in the registry) | `temperature`, `top_p`, `top_k` | `track: "reasoning"` |

**Why per-subject sampling instead of a single uniform contract**:

The original v1.0 contract — temperature=0 sent uniformly to every
provider — broke down in 2026 as frontier providers (OpenAI GPT-5.5,
Anthropic Claude Opus 4.7) started rejecting `temperature` outright,
or accepting only the platform default. Two failure modes followed:

1. Modelling every provider's per-API knob (`reasoning.effort` for
   OpenAI, `thinking.adaptive` + `output_config.effort` for Anthropic,
   `thinking_budget` for Vertex Gemini, etc.) in a single uniform
   contract would turn `subjects/registry.yaml` into a per-provider
   adapter. Every new provider release would require a schema change.
2. Forcing every model through `temperature=0` would silently drop the
   frontier of the field from the leaderboard.

Per-subject sampling separates those concerns. The `classic` mode
preserves the original contract intact: every previously evaluated
subject (GPT-5, Claude Opus 4.6, Gemini 2.5 Pro, Mistral, DeepSeek,
GPT-3.5 Turbo, …) keeps publishing under it without any methodology
change. The `reasoning` mode accepts exactly **one** portable knob —
`reasoning_effort` — which LiteLLM translates per provider, and
otherwise relies on the provider's own deterministic defaults.

**Why a single leaderboard, not two**:

This is the mainstream practice in 2026. HELM, MMLU-Pro, GPQA, Aider,
LiveBench, SWE-bench and Artificial Analysis all publish a single
ranking that mixes classic and reasoning models, documenting the
per-model sampling configuration in an appendix or annotation column
rather than partitioning the table. Splitting into two non-comparable
tables — while strictly more conservative — is out of step with the
field and degrades the legibility of the leaderboard. BluMind follows
the mainstream convention: one ranking, one table, sampling mode shown
next to each row.

**Why `reasoning_effort` is the only knob**:

Adopting `reasoning_effort` and ignoring everything else (verbosity,
thinking budgets, output-format hints, …) keeps the reasoning mode
comparable across providers and keeps the registry portable. The
benchmark accepts that reasoning-mode results are inherently less
bit-perfect than classic ones — it embraces the providers' own
definition of "deterministic enough" — in exchange for being able to
evaluate models that simply cannot run on the classic contract any
more. The `track` field on every response is preserved so leaderboard
readers and downstream analyses can isolate or filter by mode at any
time.

**Validator enforcement**: `scripts/validate_registry.py` rejects any
`kind: llm` version without a `sampling_policy` block, and rejects
`{kind: classic, reasoning_effort: ...}` (a knob that has no effect on
a classic run is most likely an authoring mistake). The JSON Schema
(`system/schemas/v1.0/registry.schema.json`) carries the binding
documentation for which fields are allowed under each kind.

**Migration**: every response file generated before this section was
introduced is `track: "classic"` by definition (the only contract that
existed at the time). The migration was done in-place by re-writing
all `responses/v1.0/**/*.json` files to include a `track: "classic"`
field next to `served_model`. The leaderboard builder treats absent
`track` as `classic` for forward compatibility, but new responses are
always emitted with the field present.
