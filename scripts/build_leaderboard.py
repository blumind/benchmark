"""
scripts/build_leaderboard.py — Render the public Markdown leaderboard
for a given BluMind benchmark version.

Inputs:
  results/metrics_per_subject.csv      (from compute_metrics.py)
  results/operational_per_subject.csv  (from compute_operational.py)
  subjects/registry.yaml               (for provider + sampling mode)
  scoring/<version>/*/*.json           (for critical-fail citations)

Output:
  results/leaderboard.md

Usage:
  python scripts/build_leaderboard.py
  python scripts/build_leaderboard.py --version v1.0 --output results/leaderboard.md
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML required (pip install pyyaml).", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v1.0"
SOURCE_SCRIPTS = [
    "scripts/compute_metrics.py",
    "scripts/compute_operational.py",
    "scripts/build_leaderboard.py",
]
QUOTE_RE = re.compile(r"['\"\u2018\u201c]([^'\"\u2019\u201d]{8,}?)['\"\u2019\u201d]")


# ---------- loaders -----------------------------------------------------------

def load_registry(path: Path) -> dict[str, dict]:
    with path.open() as f:
        data = yaml.safe_load(f)
    out: dict[str, dict] = {}
    for s in data.get("subjects", []):
        out[s["subject_id"]] = {
            "provider": s.get("provider", "—"),
            "kind": s.get("kind", "llm"),
            "versions": {v["subject_version"]: v for v in s.get("versions", [])},
        }
    return out


def load_metrics(path: Path) -> list[dict]:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: float(r["q_final"]), reverse=True)
    return rows


def load_operational(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    with path.open() as f:
        return {(r["subject_id"], r["subject_version"]): r for r in csv.DictReader(f)}


def find_critical_fails(scoring_dir: Path) -> list[dict]:
    out: list[dict] = []
    for sjson in sorted(scoring_dir.glob("*/*.json")):
        try:
            data = json.loads(sjson.read_text())
        except json.JSONDecodeError:
            continue
        for f in data.get("automatic_fails_triggered") or []:
            if f.get("severity") != "critical":
                continue
            ref = data.get("response_ref", {})
            quote = _extract_quote(f.get("justification", "")) or f.get("reference") or "—"
            out.append({
                "subject_id": ref.get("subject_id", "?"),
                "case_id": ref.get("case_id", "?"),
                "cited_action": _truncate(quote, 110),
            })
    out.sort(key=lambda x: (x["subject_id"], x["case_id"]))
    return out


def _extract_quote(text: str) -> str | None:
    m = QUOTE_RE.search(text)
    return m.group(1).strip() if m else None


def _truncate(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _f(value) -> float:
    """Parse a CSV cell into float, treating blank/None as 0.0."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "n/a"


def _mode_for(row: dict, registry: dict) -> str:
    sub = registry.get(row["subject_id"], {})
    versions = sub.get("versions", {})
    v = versions.get(row["subject_version"]) or next(iter(versions.values()), {})
    kind = ((v or {}).get("sampling_policy") or {}).get("kind", "classic")
    return "🧠 reasoning" if kind == "reasoning" else "classic"


def _provider_for(row: dict, registry: dict) -> str:
    return registry.get(row["subject_id"], {}).get("provider", "—")


def _status_badge(status: str) -> str:
    return "⛔ Disqualified" if status.lower() == "disqualified" else "✅ Eligible"


def _latest_scoring_timestamp(scoring_dir: Path) -> str:
    latest = None
    for sjson in scoring_dir.glob("*/*.json"):
        try:
            ts = json.loads(sjson.read_text()).get("scoring_timestamp_utc")
        except json.JSONDecodeError:
            continue
        if ts and (latest is None or ts > latest):
            latest = ts
    return (latest or datetime.now(timezone.utc).isoformat())[:10]


# ---------- renderers ---------------------------------------------------------

CORE_FAMILIES_V1 = ("FOUL", "SCAL", "OXID", "MECH", "NOWE")


def render_header(
    version: str,
    n_subjects: int,
    n_cases: int,
    last_update: str,
    families: list[str],
) -> str:
    if set(families) == set(CORE_FAMILIES_V1):
        coverage = (
            f"> {version} covers the **5 core failure families** "
            f"(FOUL, SCAL, OXID, MECH, NOWE) within reverse-osmosis (RO) "
            f"desalination plants — {n_cases} cases. Expansion to other water "
            f"treatment sub-sectors is planned for v2.0+.\n"
        )
    else:
        fams = ", ".join(families) if families else "—"
        coverage = (
            f"> {version} coverage so far: **{fams}** within reverse-osmosis (RO) "
            f"desalination plants — {n_cases} cases.\n"
        )
    return (
        f"# BluMind Benchmark — Leaderboard {version}\n\n"
        f"> **The first public benchmark of diagnostic and reasoning capability of\n"
        f"> AI models applied to water treatment plant operations.**\n"
        f">\n"
        + coverage
        + f"> Each model produces a single-shot JSON response under fixed sampling, scored\n"
        f"> 0–12 by the BluMind Technical Committee against a private gold standard.\n\n"
        f"**Last update**: {last_update} · **Benchmark version**: {version} · "
        f"**Subjects**: {n_subjects} · **Cases**: {n_cases} · "
        f"**Reviewer**: BluMind Technical Committee\n\n---\n\n"
    )


def render_ranking(metrics: list[dict], registry: dict, top_bold: int = 2) -> str:
    head = (
        "## 🏆 Ranking\n\n"
        "| #  | Subject | Provider | Mode | Pass | Cond | Fail | Crit | Mean (/12) | Brier ↓ | ECE ↓ | **Q ↑** | Status |\n"
        "|---:|---------|----------|------|-----:|-----:|-----:|-----:|-----------:|--------:|------:|--------:|--------|\n"
    )
    lines = []
    for i, r in enumerate(metrics, start=1):
        sid = r["subject_id"]
        provider = _provider_for(r, registry)
        mode = _mode_for(r, registry)
        crit = int(r["n_critical_fails"])
        crit_cell = f"**{crit}**" if crit > 0 else str(crit)
        mean = f"{float(r['mean_clipped_score']):.2f}"
        brier = f"{float(r['brier']):.3f}"
        ece = f"{float(r['ece']):.3f}"
        q = f"{float(r['q_final']):.2f}"
        sid_cell = f"**{sid}**" if i <= top_bold else sid
        q_cell = f"**{q}**" if i <= top_bold else q
        lines.append(
            f"| {i} | {sid_cell} | {provider} | {mode} | "
            f"{r['n_pass']} | {r['n_conditional']} | {r['n_fail']} | {crit_cell} | "
            f"{mean} | {brier} | {ece} | {q_cell} | {_status_badge(r['leaderboard_status'])} |"
        )
    return head + "\n".join(lines) + "\n\n---\n\n"


def render_operational(metrics: list[dict], operational: dict) -> str:
    head = (
        "## ⚙️ Operational characteristics\n\n"
        "| Subject | Mean tokens in | Mean tokens out | I/O ratio | Median latency | p95 latency | Cost / case |\n"
        "|---------|---------------:|----------------:|----------:|---------------:|------------:|------------:|\n"
    )
    lines = []
    for r in metrics:
        op = operational.get((r["subject_id"], r["subject_version"]))
        if not op:
            lines.append(f"| {r['subject_id']} | — | — | — | — | — | — |")
            continue
        ti = _f(op.get("mean_input_tokens"))
        to = _f(op.get("mean_output_tokens"))
        ratio = _f(op.get("output_to_input_ratio"))
        mlat = _f(op.get("median_latency_s"))
        p95 = _f(op.get("p95_latency_s"))
        pi = _f(op.get("price_per_input_token_usd"))
        po = _f(op.get("price_per_output_token_usd"))
        cost_cell = f"${ti * pi + to * po:.4f}" if (pi or po) else "—"
        lines.append(
            f"| {r['subject_id']} | {int(round(ti)):,} | {int(round(to)):,} | "
            f"{ratio:.2f} | {mlat:.0f} s | {p95:.0f} s | {cost_cell} |"
        )
    note = (
        "\n\n*Reasoning-mode subjects include the model's internal reasoning tokens "
        "in `tokens out`. Cost calculated at provider list price at the time of the run.*\n\n---\n\n"
    )
    return head + "\n".join(lines) + note


def render_disqualified(critical_fails: list[dict]) -> str:
    head = (
        "## ⛔ Disqualified subjects\n\n"
        "The **safety gate** disqualifies any subject that triggers ≥ 1 critical "
        "automatic fail in any case (e.g. recommending an oxidant on poliamide "
        "membranes). They are still listed in the ranking for transparency, with "
        "the triggering action cited literally below.\n\n"
        "| Subject | Case | Cited action that triggered the critical fail |\n"
        "|---------|------|-----------------------------------------------|\n"
    )
    if not critical_fails:
        return head + "| *(none in this benchmark run)* | — | — |\n\n---\n\n"
    lines = [
        f"| {cf['subject_id']} | {cf['case_id']} | *\"{cf['cited_action']}\"* |"
        for cf in critical_fails
    ]
    return head + "\n".join(lines) + "\n\n---\n\n"


def render_legend() -> str:
    return (
        "## 📚 How to read this leaderboard\n\n"
        "| Column | Meaning |\n"
        "|--------|---------|\n"
        "| **Pass / Cond / Fail** | Classification per case using `rubric_floor` / `rubric_ceiling`. |\n"
        "| **Crit** | Critical automatic fails. ≥ 1 → `Disqualified` from the safety gate. |\n"
        "| **Mean (/12)** | Average clipped score per case (rubric ceiling = 12). |\n"
        "| **Brier ↓** | Brier calibration error (0 = perfectly calibrated, 1 = worst). |\n"
        "| **ECE ↓** | Expected calibration error (0 = perfectly calibrated, 1 = worst). |\n"
        "| **Q ↑** | Composite quality score. The ranking column. |\n"
        "| **Mode** | `classic` = `temperature=0` sent. `reasoning` = provider's deterministic defaults + `reasoning_effort`. |\n\n---\n\n"
    )


def render_links() -> str:
    src = ", ".join(f"[`{p}`]({p})" for p in SOURCE_SCRIPTS)
    return (
        "## 🔗 Methodology & sources\n\n"
        "- **Rubric & metrics**: [`docs/methodology.md`](docs/methodology.md)\n"
        "- **Sampling policy** (classic vs reasoning): [`docs/run_evaluation_design.md`](docs/run_evaluation_design.md) § 7\n"
        "- **Submit a model**: [`docs/submission_guide.md`](docs/submission_guide.md)\n"
        f"- **Source code**: {src}\n"
        "- **Public site**: <https://benchmark.blumind.es>\n"
        "- **Repo**: <https://github.com/blumind/benchmark>\n\n---\n\n"
    )


def render_footer(git_sha: str, timestamp: str) -> str:
    return (
        f"*Generated automatically by `scripts/build_leaderboard.py` from "
        f"`results/metrics_per_subject.csv` and `results/operational_per_subject.csv` "
        f"on {timestamp} (commit {git_sha}).*\n"
    )


# ---------- main --------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Build BluMind public Markdown leaderboard.")
    p.add_argument("--version", default=DEFAULT_VERSION)
    p.add_argument("--metrics", type=Path, default=REPO_ROOT / "results/metrics_per_subject.csv")
    p.add_argument("--operational", type=Path, default=REPO_ROOT / "results/operational_per_subject.csv")
    p.add_argument("--registry", type=Path, default=REPO_ROOT / "subjects/registry.yaml")
    p.add_argument("--scoring-dir", type=Path, default=None)
    p.add_argument("--output", type=Path, default=REPO_ROOT / "results/leaderboard.md")
    p.add_argument("--top-bold", type=int, default=2)
    args = p.parse_args()

    scoring_dir = args.scoring_dir or (REPO_ROOT / f"scoring/{args.version}")
    if not args.metrics.exists():
        print(f"error: metrics file not found: {args.metrics}", file=sys.stderr)
        return 2

    registry = load_registry(args.registry)
    metrics = load_metrics(args.metrics)
    operational = load_operational(args.operational)
    critical_fails = find_critical_fails(scoring_dir)
    case_ids = {Path(p).stem.split("__")[0] for p in scoring_dir.glob("*/*.json")}
    n_cases = len(case_ids)
    families = sorted({cid.split("-")[1] for cid in case_ids if cid.count("-") >= 2})
    last_update = _latest_scoring_timestamp(scoring_dir)

    parts = [
        render_header(args.version, len(metrics), n_cases, last_update, families),
        render_ranking(metrics, registry, top_bold=args.top_bold),
        render_operational(metrics, operational),
        render_disqualified(critical_fails),
        render_legend(),
        render_links(),
        render_footer(_git_sha(), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(parts))
    print(f"wrote {args.output} ({len(metrics)} subjects, {len(critical_fails)} critical fails)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
