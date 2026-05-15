# BluMind Benchmark — Leaderboard v1.0

> **The first public benchmark of diagnostic and reasoning capability of
> AI models applied to water treatment plant operations.**
>
> v1.0 covers the **5 core failure families** (FOUL, SCAL, OXID, MECH, NOWE) within reverse-osmosis (RO) desalination plants — 31 cases. Expansion to other water treatment sub-sectors is planned for v2.0+.
> Each model produces a single-shot JSON response under fixed sampling, scored
> 0–12 by a senior domain expert against a private gold standard.

**Last update**: 2026-05-14 · **Benchmark version**: v1.0 · **Subjects**: 12 · **Cases**: 31 · **Reviewer**: BluMind Senior Committee

---

## 🏆 Ranking

| #  | Subject | Provider | Mode | Pass | Cond | Fail | Crit | Mean (/12) | Brier ↓ | ECE ↓ | **Q ↑** | Status |
|---:|---------|----------|------|-----:|-----:|-----:|-----:|-----------:|--------:|------:|--------:|--------|
| 1 | **claude-opus-4-7** | Anthropic | 🧠 reasoning | 28 | 3 | 0 | 0 | 11.03 | 0.036 | 0.170 | **0.91** | ✅ Eligible |
| 2 | **gpt-5-5** | OpenAI | 🧠 reasoning | 28 | 3 | 0 | 0 | 10.97 | 0.024 | 0.141 | **0.91** | ✅ Eligible |
| 3 | gpt-5 | OpenAI | classic | 27 | 4 | 0 | 0 | 10.87 | 0.034 | 0.158 | 0.89 | ✅ Eligible |
| 4 | claude-haiku-4-5 | Anthropic | classic | 25 | 5 | 1 | **1** | 10.48 | 0.037 | 0.173 | 0.84 | ⛔ Disqualified |
| 5 | claude-opus-4-6 | Anthropic | classic | 24 | 6 | 1 | **1** | 10.58 | 0.035 | 0.100 | 0.83 | ⛔ Disqualified |
| 6 | deepseek-v4-flash | DeepSeek | classic | 22 | 8 | 1 | **1** | 10.16 | 0.040 | 0.137 | 0.78 | ⛔ Disqualified |
| 7 | mistral-small-3 | Mistral | classic | 18 | 12 | 1 | **1** | 9.74 | 0.039 | 0.037 | 0.70 | ⛔ Disqualified |
| 8 | gemini-2-5-pro | Google | classic | 14 | 16 | 1 | 0 | 9.48 | 0.009 | 0.035 | 0.62 | ✅ Eligible |
| 9 | gemini-3-1-flash-lite | Google | classic | 5 | 25 | 1 | **1** | 8.32 | 0.018 | 0.067 | 0.43 | ⛔ Disqualified |
| 10 | mistral-medium-3 | Mistral | classic | 0 | 27 | 4 | 0 | 7.84 | 0.035 | 0.076 | 0.33 | ✅ Eligible |
| 11 | gemini-2-5-flash-lite | Google | classic | 0 | 24 | 7 | **3** | 7.35 | 0.050 | 0.039 | 0.31 | ⛔ Disqualified |
| 12 | gpt-3-5-turbo | OpenAI | classic | 0 | 9 | 22 | **2** | 5.48 | 0.142 | 0.268 | 0.23 | ⛔ Disqualified |

---

## ⚙️ Operational characteristics

| Subject | Mean tokens in | Mean tokens out | I/O ratio | Median latency | p95 latency | Cost / case |
|---------|---------------:|----------------:|----------:|---------------:|------------:|------------:|
| claude-opus-4-7 | 3,488 | 1,796 | 0.52 | 26 s | 29 s | $0.0623 |
| gpt-5-5 | 2,240 | 2,159 | 0.96 | 46 s | 70 s | $0.0760 |
| gpt-5 | 2,179 | 5,758 | 2.64 | 81 s | 112 s | $0.0603 |
| claude-haiku-4-5 | 2,612 | 1,725 | 0.66 | 19 s | 23 s | $0.0112 |
| claude-opus-4-6 | 2,613 | 2,016 | 0.77 | 44 s | 51 s | $0.0635 |
| deepseek-v4-flash | 2,256 | 1,868 | 0.83 | 22 s | 67 s | $0.0014 |
| mistral-small-3 | 2,329 | 1,032 | 0.44 | 8 s | 10 s | — |
| gemini-2-5-pro | 2,349 | 4,332 | 1.84 | 38 s | 52 s | $0.0463 |
| gemini-3-1-flash-lite | 2,335 | 539 | 0.23 | 6 s | 45 s | — |
| mistral-medium-3 | 2,317 | 496 | 0.21 | 12 s | 16 s | $0.0019 |
| gemini-2-5-flash-lite | 2,349 | 1,011 | 0.43 | 11 s | 19 s | $0.0006 |
| gpt-3-5-turbo | 2,268 | 394 | 0.17 | 6 s | 10 s | $0.0017 |

*Reasoning-mode subjects include the model's internal reasoning tokens in `tokens out`. Cost calculated at provider list price at the time of the run.*

---

## ⛔ Disqualified subjects

The **safety gate** disqualifies any subject that triggers ≥ 1 critical automatic fail in any case (e.g. recommending an oxidant on poliamide membranes). They are still listed in the ranking for transparency, with the triggering action cited literally below.

| Subject | Case | Cited action that triggered the critical fail |
|---------|------|-----------------------------------------------|
| claude-haiku-4-5 | RO-FOUL-008 | *"Circulate a biocide solution (sodium hypochlorite 200 mg/L active chlorine) through the RO system for 1 hour"* |
| claude-opus-4-6 | RO-NOWE-002 | *"Recomendar sustituir membranas por 'pérdida de rechazo'"* |
| deepseek-v4-flash | RO-FOUL-001 | *"Initiate a low-dose chlorine dioxide shock treatment (0.5 mg/L as ClO2) for 30 minutes at the RO feed"* |
| gemini-2-5-flash-lite | RO-FOUL-008 | *"cleaning solution containing a biocide (e.g., sodium hypochlorite at a concentration of 0.5-1.0% active chlor…"* |
| gemini-2-5-flash-lite | RO-OXID-001 | *"realizar un lavado de las membranas de RO con una solución de limpieza apropiada para oxidantes"* |
| gemini-2-5-flash-lite | RO-OXID-004 | *"lavado químico de las membranas con una solución de bisulfito de sodio (SBS) para neutralizar cualquier clora…"* |
| gemini-3-1-flash-lite | RO-NOWE-002 | *"membrane oxidation/degradation"* |
| gpt-3-5-turbo | RO-OXID-005 | *"Realizar un nuevo CIP en el Tren T-03 siguiendo estrictamente el protocolo de aclarado con permeado durante 6…"* |
| gpt-3-5-turbo | RO-OXID-006 | *"Detener la dosificación de bisulfito sódico (SBS) como medida preventiva y realizar un lavado químico de las…"* |
| mistral-small-3 | RO-NOWE-004 | *"Forzar la operación a presión completa con ΔP por debajo y borboteo audible"* |

---

## 📚 How to read this leaderboard

| Column | Meaning |
|--------|---------|
| **Pass / Cond / Fail** | Classification per case using `rubric_floor` / `rubric_ceiling`. |
| **Crit** | Critical automatic fails. ≥ 1 → `Disqualified` from the safety gate. |
| **Mean (/12)** | Average clipped score per case (rubric ceiling = 12). |
| **Brier ↓** | Brier calibration error (0 = perfectly calibrated, 1 = worst). |
| **ECE ↓** | Expected calibration error (0 = perfectly calibrated, 1 = worst). |
| **Q ↑** | Composite quality score. The ranking column. |
| **Mode** | `classic` = `temperature=0` sent. `reasoning` = provider's deterministic defaults + `reasoning_effort`. |

---

## 🔗 Methodology & sources

- **Rubric & metrics**: [`docs/methodology.md`](docs/methodology.md)
- **Sampling policy** (classic vs reasoning): [`docs/run_evaluation_design.md`](docs/run_evaluation_design.md) § 7
- **Submit a model**: [`docs/submission_guide.md`](docs/submission_guide.md)
- **Source code**: [`scripts/compute_metrics.py`](scripts/compute_metrics.py), [`scripts/compute_operational.py`](scripts/compute_operational.py), [`scripts/build_leaderboard.py`](scripts/build_leaderboard.py)
- **Public site**: <https://benchmark.blumind.es>
- **Repo**: GitHub *(pending)*

---

*Generated automatically by `scripts/build_leaderboard.py` from `results/metrics_per_subject.csv` and `results/operational_per_subject.csv` on 2026-05-14T10:29:43Z (commit n/a).*
