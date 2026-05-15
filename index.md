---
layout: default
title: BluMind Benchmark
description: The public benchmark of AI reasoning applied to water-treatment-plant operations.
lang: en
---

# BluMind Benchmark

**The public benchmark of AI reasoning applied to water-treatment-plant operations.**

BluMind evaluates AI models on real diagnostic and reasoning tasks drawn from the operation of water-treatment plants. Every response is scored by the **BluMind Technical Committee** — senior practitioners and researchers of the water sector — against a private gold standard.

The benchmark is **public, reproducible, and human-scored**. The leaderboard updates as new models are submitted and as the Technical Committee releases new cases.

---

## 🏆 Ranking · v1.0

v1.0 covers the **5 core failure families** (FOUL, SCAL, OXID, MECH, NOWE) of reverse-osmosis desalination plants — **31 cases**, **12 models evaluated**, scored by the BluMind Technical Committee.

<div style="overflow-x: auto;" markdown="1">

| #  | Subject | Provider | Mode | Pass | Cond | Fail | Crit | Mean (/12) | Brier ↓ | ECE ↓ | **Q ↑** | Status |
|---:|---------|----------|:----:|-----:|-----:|-----:|-----:|-----------:|--------:|------:|--------:|:------:|
| 1  | **claude-opus-4-7** | Anthropic | 🧠 reasoning | 28 | 3  | 0  | 0   | 11.03 | 0.036 | 0.170 | **0.91** | ✅ Eligible |
| 2  | **gpt-5-5** | OpenAI | 🧠 reasoning | 28 | 3  | 0  | 0   | 10.97 | 0.024 | 0.141 | **0.91** | ✅ Eligible |
| 3  | gpt-5 | OpenAI | classic | 27 | 4  | 0  | 0   | 10.87 | 0.034 | 0.158 | 0.89 | ✅ Eligible |
| 4  | claude-haiku-4-5 | Anthropic | classic | 25 | 5  | 1  | **1** | 10.48 | 0.037 | 0.173 | 0.84 | ⛔ Disqualified |
| 5  | claude-opus-4-6 | Anthropic | classic | 24 | 6  | 1  | **1** | 10.58 | 0.035 | 0.100 | 0.83 | ⛔ Disqualified |
| 6  | deepseek-v4-flash | DeepSeek | classic | 22 | 8  | 1  | **1** | 10.16 | 0.040 | 0.137 | 0.78 | ⛔ Disqualified |
| 7  | mistral-small-3 | Mistral | classic | 18 | 12 | 1  | **1** | 9.74 | 0.039 | 0.037 | 0.70 | ⛔ Disqualified |
| 8  | gemini-2-5-pro | Google | classic | 14 | 16 | 1  | 0   | 9.48 | 0.009 | 0.035 | 0.62 | ✅ Eligible |
| 9  | gemini-3-1-flash-lite | Google | classic | 5 | 25 | 1  | **1** | 8.32 | 0.018 | 0.067 | 0.43 | ⛔ Disqualified |
| 10 | mistral-medium-3 | Mistral | classic | 0 | 27 | 4  | 0   | 7.84 | 0.035 | 0.076 | 0.33 | ✅ Eligible |
| 11 | gemini-2-5-flash-lite | Google | classic | 0 | 24 | 7  | **3** | 7.35 | 0.050 | 0.039 | 0.31 | ⛔ Disqualified |
| 12 | gpt-3-5-turbo | OpenAI | classic | 0 | 9 | 22 | **2** | 5.48 | 0.142 | 0.268 | 0.23 | ⛔ Disqualified |

</div>

### 📚 How to read this table

- **Pass / Cond / Fail** — Per-case classification by the Technical Committee. **Pass** = a response an experienced operator would accept on its own. **Conditional** = a response with gaps but salvageable. **Fail** = a response that would mislead a real operator.
- **Crit** — Critical automatic fails. Cases where the response recommended an action that would damage the plant or compromise operator safety (for example, recommending an oxidant on polyamide membranes). **A single critical fail disqualifies the model from the leaderboard**, regardless of all other scores. The triggering action is cited literally in the full leaderboard on GitHub.
- **Mean (/12)** — Average expert-scored quality per case, on the 0–12 rubric. 12 = "indistinguishable from the expert gold answer"; 0 = "completely wrong".
- **Brier ↓** and **ECE ↓** — Both measure **confidence calibration**: whether the model knows what it knows. Imagine an operator who says *"I'm 90 % sure this is biofouling"*: if they are right 90 times out of 100 when they say that, they are well-calibrated. If they say 90 % but are right only 60 times out of 100, they are overconfident and dangerous to trust. **Lower is better.** This matters when downstream decisions weigh the model's confidence — automated alarms, advisory systems, or any pipeline that takes "I am 95 % sure" at face value.
- **Q ↑** — Composite quality score combining Pass-rate and mean per-case score. This is the ranking column.
- **Mode** — `classic` means the model was queried at `temperature = 0`. 🧠 `reasoning` means the model was queried using its native deep-thinking mode (Claude reasoning, GPT reasoning, etc.).
- **Status** — ✅ **Eligible** if the model has zero critical fails. ⛔ **Disqualified** otherwise. Disqualified models are still listed for transparency, but they cannot win the leaderboard.

[See operational metrics (cost, latency, tokens) and safety-gate citations on GitHub →](https://github.com/blumind/benchmark/blob/main/results/leaderboard.md)

---

## What makes BluMind different

**Independent human scoring.** Every response is scored by **two members** of the BluMind Technical Committee, drawn from senior practitioners and researchers of the water sector. The committee is the institutional authority behind every score.

**Safety gate.** A single critical-fail recommendation — any action that would damage the plant or compromise operator safety — disqualifies the model from the leaderboard regardless of its other scores. The triggering action is cited literally and made public.

**Reproducible.** Cases, rubric, prompts, evaluation scripts and aggregated metrics are public. The private gold answers and reviewer mappings stay private — exactly as one would expect from a benchmark that can be trusted.

[Read the full methodology on GitHub →](https://github.com/blumind/benchmark/blob/main/docs/methodology.md)

---

## Submit a model

During the **foundational phase** (until 31 December 2026), valid submissions are evaluated **free of charge**. The submitter provides metadata, technical access credentials encrypted with the BluMind PGP key, and confirms eligibility against the published scope.

A submission is normally validated within **2 working days** and evaluated within **10 working days** of validation.

[Read the submission guide on GitHub →](https://github.com/blumind/benchmark/blob/main/docs/submission_guide.md)

---

## The committee

The **BluMind Technical Committee** is the body of senior practitioners and researchers responsible for the integrity of the benchmark. It is the institutional authority behind every score, classification, and appeal decision.

Public members include **Álvaro Díaz del Río Redondo** — CEO of BluMind, formerly Head of Innovation at Tedagua and Cobra Infraestructuras Hidráulicas — and **Rafael Jiménez Garrido** — Country Manager at Whitewater Group, lecturer at the Master's Degree in Desalination and Water Reuse (Universidad de Alicante), industry contributor at ALADYR.

Three additional senior international figures of the water sector are part of the committee, with names pending public disclosure.

[Meet the committee on GitHub →](https://github.com/blumind/benchmark/blob/main/COMMITTEE.md)

---

## Contact

- Submissions: [submissions@blumind.es](mailto:submissions@blumind.es) · [PGP public key](https://github.com/blumind/benchmark/blob/main/system/keys/blumind-submissions.asc)
- Technical Committee: [committee@blumind.es](mailto:committee@blumind.es)
- General inquiries: [info@blumind.es](mailto:info@blumind.es)
- Repository: [github.com/blumind/benchmark](https://github.com/blumind/benchmark)

---

<p style="font-size: 0.85em; color: #122c4b;">BluMind Benchmark is operated by BluMind. The benchmark is released under the license terms in <a href="https://github.com/blumind/benchmark/blob/main/LICENSE">LICENSE</a>.</p>
