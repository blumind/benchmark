---
layout: default
title: BluMind Benchmark
description: The public benchmark of AI reasoning applied to water-treatment-plant operations.
---

<p style="text-align: right; font-size: 0.9em; color: #666; margin-bottom: 1.5em;"><strong>English</strong> &nbsp;·&nbsp; <a href="/es/">Español</a></p>

# BluMind Benchmark

**The public benchmark of AI reasoning applied to water-treatment-plant operations — in Spanish.**

BluMind evaluates AI models on real diagnostic and reasoning tasks drawn from the operation of water-treatment plants. Every response is scored by the **BluMind Technical Committee** — senior practitioners and researchers of the water sector — against a private gold standard.

The benchmark is **public, reproducible, and human-scored**. The leaderboard updates as new models are submitted.

---

## Leaderboard · v1.0

v1.0 covers the **5 core failure families** (FOUL, SCAL, OXID, MECH, NOWE) of reverse-osmosis desalination plants — **31 cases**, **12 models evaluated**, scored by the BluMind Technical Committee.

| #  | Subject | Provider | Mode | Mean (/12) | **Q ↑** | Status |
|---:|---------|----------|:----:|-----------:|--------:|:------:|
| 1 | **claude-opus-4-7** | Anthropic | reasoning | 11.03 | **0.91** | Eligible |
| 2 | **gpt-5-5** | OpenAI | reasoning | 10.97 | **0.91** | Eligible |
| 3 | gpt-5 | OpenAI | classic | 10.87 | 0.89 | Eligible |
| 4 | claude-haiku-4-5 | Anthropic | classic | 10.48 | 0.84 | Disqualified |
| 5 | claude-opus-4-6 | Anthropic | classic | 10.58 | 0.83 | Disqualified |

*Top 5 by composite quality score Q. **Disqualified** models triggered the safety gate on at least one case.*

[See the full leaderboard, operational costs, and safety-gate details on GitHub →](https://github.com/blumind/benchmark/blob/main/results/leaderboard.md)

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

<p style="font-size: 0.85em; color: #666;">BluMind Benchmark is operated by BluMind. The benchmark is released under the license terms in <a href="https://github.com/blumind/benchmark/blob/main/LICENSE">LICENSE</a>.</p>
