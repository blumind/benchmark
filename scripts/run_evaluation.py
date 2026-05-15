#!/usr/bin/env python3
"""Call subject API, generate response JSON, validate, and store.

Reads a case from cases/v1.0/, builds the prompt from
system/prompts/v1.0/prompt_template.md, calls the subject's LLM API via
LiteLLM, wraps the model output with the six traceability fields, validates
against system/schemas/v1.0/response.schema.json, and writes the result to
responses/v1.0/<subject_id>/<case_id>__<run_id>.json.

Design decisions are documented in docs/run_evaluation_design.md.

Usage examples:

    # Single case, single subject:
    python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5

    # All FOUL cases on GPT-5:
    python scripts/run_evaluation.py --family FOUL --subject gpt-5

    # All cases on every LLM subject in the registry:
    python scripts/run_evaluation.py --all

    # Pin a specific subject_version (else: most recent in registry):
    python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5 \\
        --subject-version gpt-5-2026-03-15

    # Override the LiteLLM model string (e.g. for staging endpoints):
    python scripts/run_evaluation.py --case RO-FOUL-002 --subject gpt-5 \\
        --litellm-model openai/gpt-5-2026-03-15

    # Dry run: print the plan without calling any API:
    python scripts/run_evaluation.py --all --dry-run

Behaviour on errors:
  - Network/transient failures: 3 automatic retries with exponential backoff
    (handled by LiteLLM via num_retries).
  - JSON parse errors or schema validation failures: the raw model output is
    saved to responses/v1.0/<subject_id>/_errors/<case_id>__<run_id>.txt and
    a diagnostic log to <case_id>__<run_id>.error.log. The batch continues.

Exit codes: 0 if every requested run succeeded, 1 if any run failed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from _validator_common import (
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    find_repo_root,
    load_schema,
    validate_against,
)
from _runner_telemetry import (
    extract_call_metrics,
    format_cost_inline,
    print_batch_summary,
    write_batch_log,
)


BENCHMARK_VERSION = "v1.0"

PROVIDER_TO_LITELLM_PREFIX = {
    "OpenAI": "openai",
    "Anthropic": "anthropic",
    "Google": "gemini",
    "Mistral": "mistral",
    "Cohere": "cohere",
    "Together": "together_ai",
    "Groq": "groq",
    "DeepSeek": "deepseek",
    "Moonshot": "moonshot",
    "BluMind Internal": "openai",
    "BluMind Committee": "manual",
}

REQUIRED_CASE_SECTIONS = [
    "case_id",
    "plant_context",
    "operational_data",
    "recent_history",
    "reporting_party",
    "reporting_date",
]


def load_registry(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Read subjects/registry.yaml as a dict keyed by subject_id."""
    path = repo_root / "subjects" / "registry.yaml"
    if not path.is_file():
        raise SystemExit(f"ERROR: registry not found at {path}")
    data = yaml.safe_load(path.read_text())
    return {s["subject_id"]: s for s in data.get("subjects", [])}


def parse_prompt_template(path: Path) -> tuple[str, str]:
    """Extract the [SYSTEM] and [USER] verbatim blocks from prompt_template.md."""
    text = path.read_text()
    system_match = re.search(
        r"##\s*\[SYSTEM\]\s*\n+```\s*\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    user_match = re.search(
        r"##\s*\[USER\]\s*\n+```\s*\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    if not system_match or not user_match:
        raise SystemExit(
            f"ERROR: could not extract [SYSTEM] and [USER] blocks from {path}."
        )
    return system_match.group(1).strip(), user_match.group(1).strip()


def parse_case_file(path: Path) -> dict[str, str]:
    """Extract section content from a case markdown file.

    Sections are introduced by `## <name>` headings; each section's content
    runs until the next `##` heading or end-of-file.
    """
    text = path.read_text()
    sections: dict[str, str] = {}
    pattern = re.compile(r"^##\s+(\w+)\s*\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(text):
        sections[match.group(1)] = match.group(2).strip()
    missing = [name for name in REQUIRED_CASE_SECTIONS if name not in sections]
    if missing:
        raise ValueError(
            f"case file {path.name} is missing required sections: {missing}"
        )
    return sections


def build_user_prompt(template: str, case_sections: dict[str, str]) -> str:
    """Substitute {placeholders} in the user template with case content.

    Uses literal string replacement (not str.format) so braces inside the
    case content cannot break the substitution.
    """
    result = template
    for key, value in case_sections.items():
        result = result.replace("{" + key + "}", value)
    return result


def select_cases(repo_root: Path, args: argparse.Namespace) -> list[Path]:
    """Resolve which case files to evaluate based on CLI flags."""
    cases_dir = repo_root / "cases" / "v1.0"
    if not cases_dir.is_dir():
        raise SystemExit(f"ERROR: cases directory not found at {cases_dir}")
    all_cases = sorted(p for p in cases_dir.glob("RO-*.md") if not p.name.startswith("_"))
    if args.case:
        target = cases_dir / f"{args.case}.md"
        if not target.is_file():
            raise SystemExit(f"ERROR: case file not found: {target}")
        return [target]
    if args.family:
        return [c for c in all_cases if c.stem.split("-")[1] == args.family]
    return all_cases


def select_subjects(
    registry: dict[str, dict[str, Any]], args: argparse.Namespace
) -> list[str]:
    """Resolve which subjects to evaluate based on CLI flags.

    Default scope (no --subject): every entry with kind=llm. Human baselines
    are skipped automatically because their access_type is `manual`.
    """
    if args.subject:
        if args.subject not in registry:
            raise SystemExit(
                f"ERROR: subject {args.subject!r} not found in subjects/registry.yaml"
            )
        if registry[args.subject].get("kind") != "llm":
            raise SystemExit(
                f"ERROR: subject {args.subject!r} has kind={registry[args.subject].get('kind')!r}; "
                "this script only evaluates kind=llm subjects."
            )
        return [args.subject]
    return [sid for sid, s in registry.items() if s.get("kind") == "llm"]


def resolve_subject_version(
    subject: dict[str, Any], requested: str | None
) -> dict[str, Any]:
    """Return the version dict to evaluate (explicit override or latest)."""
    versions = subject["versions"]
    if requested:
        for v in versions:
            if v["subject_version"] == requested:
                return v
        raise SystemExit(
            f"ERROR: subject_version {requested!r} not registered "
            f"for subject {subject['subject_id']!r}"
        )
    return versions[-1]


def verify_served_model(served_model: str | None, expected_version: str) -> None:
    """Abort if the model actually served by the API does not match the pinned snapshot.

    This is the last line of defence against the alias-vs-snapshot drift
    that v1.0 hit once: calling ``openai/gpt-5`` (alias) routed to a
    snapshot that was not the one declared in ``subjects/registry.yaml``.
    We compare bare names (provider prefix already stripped upstream).

    Policy:
      * ``served_model`` missing → hard abort (no traceability is unacceptable).
      * ``served_model`` present and equal to ``expected_version`` → OK.
      * Otherwise → hard abort with a clear message.
    """
    if not served_model:
        raise SystemExit(
            "ERROR: provider did not return a model identifier in the API "
            f"response. Cannot verify the snapshot served. Expected "
            f"{expected_version!r}. Aborting to preserve traceability."
        )
    if served_model != expected_version:
        raise SystemExit(
            f"ERROR: served model mismatch. Requested {expected_version!r} "
            f"but the provider served {served_model!r}. Aborting the run "
            "to preserve traceability. Update subjects/registry.yaml to "
            "pin the snapshot you actually want, then retry."
        )


def litellm_model_for(
    subject_id: str,
    subject_version: str,
    provider: str,
    override: str | None = None,
) -> str:
    """Compose the LiteLLM model identifier for this subject.

    Always pins the call to the exact ``subject_version`` (a snapshot ID),
    never to the unpinned ``subject_id`` alias. This is the contract the
    runner enforces to keep ``responses/*.json`` byte-faithful to the
    snapshot recorded in ``subjects/registry.yaml``. See
    ``docs/run_evaluation_design.md`` § Traceability.
    """
    if override:
        return override
    prefix = PROVIDER_TO_LITELLM_PREFIX.get(provider)
    if not prefix:
        raise SystemExit(
            f"ERROR: unknown provider {provider!r} for subject {subject_id!r}. "
            f"Pass --litellm-model to override or extend "
            f"PROVIDER_TO_LITELLM_PREFIX in this script."
        )
    return f"{prefix}/{subject_version}"


def next_run_id(responses_dir: Path, subject_id: str, case_id: str) -> str:
    """Compute next run_id for today: run-YYYY-MM-DD-NNN."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prefix = f"run-{today}-"
    subject_dir = responses_dir / subject_id
    used: list[int] = []
    if subject_dir.is_dir():
        for f in subject_dir.glob(f"{case_id}__{prefix}*.json"):
            m = re.search(r"run-\d{4}-\d{2}-\d{2}-(\d{3})\.json$", f.name)
            if m:
                used.append(int(m.group(1)))
    next_n = (max(used) + 1) if used else 1
    return f"{prefix}{next_n:03d}"


def parse_json_from_response(text: str) -> dict[str, Any]:
    """Parse the model's textual output into a JSON dict.

    Strategy: try to parse the trimmed text directly (the prompt instructs the
    model to emit only a JSON object). If that fails because the model wrapped
    the JSON in markdown fences, strip the fences and retry. As a last resort,
    locate the outermost {...} substring and parse that. Any failure raises
    json.JSONDecodeError or ValueError (handled by the caller).
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def build_sampling_kwargs(policy: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    """Translate a registry ``sampling_policy`` block into (track, LiteLLM kwargs).

    The v1.0 benchmark publishes two parallel, non-comparable leaderboards:

    * ``classic`` (default if the block is absent, e.g. legacy entries)
      → ``temperature=0``. The original v1.0 contract documented in
      ``system/prompts/v1.0/prompt_template.md`` § EXECUTION PARAMETERS.
      ``top_p`` is intentionally omitted: with temperature=0 it is
      mathematically redundant and not portable across providers
      (Anthropic rejects it alongside temperature, newer OpenAI snapshots
      reject it outright).

    * ``reasoning`` → omit ``temperature``/``top_p``/``top_k`` entirely.
      Forward ``reasoning_effort`` only if declared. LiteLLM translates
      that single portable knob into each provider's native control:
      OpenAI GPT-5.x → ``reasoning.effort``; Anthropic Claude Opus 4.7
      → ``thinking.adaptive`` + ``output_config.effort``; etc.

    Returning the track string alongside the kwargs lets the caller stamp
    every response.json with the track it was produced under, so the
    leaderboard builder can route results into the correct table.
    """
    if not policy:
        return "classic", {"temperature": 0}
    kind = policy.get("kind", "classic")
    if kind == "classic":
        return "classic", {"temperature": 0}
    if kind == "reasoning":
        kwargs: dict[str, Any] = {}
        if "reasoning_effort" in policy:
            kwargs["reasoning_effort"] = policy["reasoning_effort"]
        return "reasoning", kwargs
    raise SystemExit(
        f"ERROR: unknown sampling_policy.kind={kind!r}. "
        "Allowed values: 'classic', 'reasoning'."
    )


def call_model(
    litellm_model: str,
    system_prompt: str,
    user_prompt: str,
    num_retries: int,
    sampling_kwargs: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Call LiteLLM and return (raw text, call metrics).

    The sampling kwargs (temperature / reasoning_effort / verbosity / …)
    are computed upstream from each subject's ``sampling_policy`` block in
    ``subjects/registry.yaml`` — see :func:`build_sampling_kwargs` and
    ``docs/run_evaluation_design.md`` § Sampling policy. We always set
    ``litellm.drop_params = True`` as a safety net for any provider-side
    unsupported parameter that LiteLLM might inject by default.

    The returned metrics dict has these keys (any may be ``None`` if the
    provider did not return usage info or LiteLLM has no pricing entry):
    ``prompt_tokens``, ``completion_tokens``, ``total_tokens``,
    ``cost_usd``, ``latency_ms``, ``served_model``.
    """
    try:
        import litellm
    except ImportError as e:
        raise SystemExit(
            "ERROR: litellm is not installed. Run "
            "'pip install -r scripts/requirements.txt'."
        ) from e

    litellm.drop_params = True

    t0 = time.perf_counter()
    response = litellm.completion(
        model=litellm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        num_retries=num_retries,
        **sampling_kwargs,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)

    metrics = extract_call_metrics(response, latency_ms, litellm, litellm_model)
    text = response["choices"][0]["message"]["content"]
    return text, metrics


def utc_iso_now() -> str:
    """UTC timestamp in ISO-8601 with 'Z' suffix (date-time per JSON Schema)."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def save_success(
    responses_dir: Path, subject_id: str, case_id: str, run_id: str, payload: dict[str, Any]
) -> Path:
    """Persist a validated response JSON. Returns the final path."""
    out_dir = responses_dir / subject_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{case_id}__{run_id}.json"
    out_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_file


def save_error(
    responses_dir: Path,
    subject_id: str,
    case_id: str,
    run_id: str,
    raw_text: str | None,
    error_message: str,
) -> Path:
    """Persist a failed run: raw model output + diagnostic log."""
    err_dir = responses_dir / subject_id / "_errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    raw_file = err_dir / f"{case_id}__{run_id}.txt"
    log_file = err_dir / f"{case_id}__{run_id}.error.log"
    raw_file.write_text(
        raw_text if raw_text is not None else "<no response captured>",
        encoding="utf-8",
    )
    log_file.write_text(error_message + "\n", encoding="utf-8")
    return err_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the BluMind Benchmark pipeline against one or more LLM subjects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--case",
        metavar="CASE_ID",
        help="Single case (e.g. RO-FOUL-002). Mutually exclusive with --family.",
    )
    parser.add_argument(
        "--family",
        metavar="FAMILY",
        choices=["OXID", "SCAL", "FOUL", "MECH", "NOWE"],
        help="Filter cases by family code. Mutually exclusive with --case.",
    )
    parser.add_argument(
        "--subject",
        metavar="SUBJECT_ID",
        help="Single subject_id from subjects/registry.yaml (e.g. gpt-5). "
        "If omitted, all kind=llm subjects are evaluated.",
    )
    parser.add_argument(
        "--subject-version",
        metavar="SUBJECT_VERSION",
        help="Pin a specific subject_version. Defaults to the most recent "
        "version registered for the subject.",
    )
    parser.add_argument(
        "--litellm-model",
        metavar="MODEL_STRING",
        help="Override the LiteLLM model identifier "
        "(e.g. 'openai/gpt-5-2026-03-15').",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Required to run with no filters (every case × every LLM subject).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of automatic retries with exponential backoff (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the execution plan and exit without calling any API.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.case and args.family:
        raise SystemExit("ERROR: --case and --family are mutually exclusive.")

    no_filters = not (args.case or args.family or args.subject)
    if no_filters and not args.all:
        raise SystemExit(
            "ERROR: no filters provided. Pass --all to evaluate every case × "
            "every LLM subject, or narrow scope with --case / --family / --subject."
        )

    repo_root = find_repo_root()
    load_dotenv(repo_root / ".env")

    response_schema = load_schema(repo_root, "response")
    registry = load_registry(repo_root)
    system_prompt, user_template = parse_prompt_template(
        repo_root / "system" / "prompts" / "v1.0" / "prompt_template.md"
    )

    cases = select_cases(repo_root, args)
    subjects = select_subjects(registry, args)

    total_runs = len(cases) * len(subjects)
    if total_runs == 0:
        print(f"{COLOR_YELLOW}No runs to execute (empty case or subject set).{COLOR_RESET}")
        return 0

    print(
        f"Plan: {len(cases)} case(s) × {len(subjects)} subject(s) "
        f"= {total_runs} run(s). benchmark_version={BENCHMARK_VERSION}."
    )
    if args.dry_run:
        print("(dry run; no API calls performed)")
        for c in cases:
            for s in subjects:
                print(f"  - {c.stem}  →  {s}")
        return 0

    responses_dir = repo_root / "responses" / BENCHMARK_VERSION
    passed = failed = 0
    run_index = 0
    batch_rows: list[dict[str, Any]] = []

    for case_path in cases:
        try:
            case_sections = parse_case_file(case_path)
        except Exception as exc:
            print(f"{COLOR_RED}SKIP{COLOR_RESET}  {case_path.name}: {exc}")
            failed += len(subjects)
            run_index += len(subjects)
            continue

        case_id = case_sections["case_id"]
        user_prompt = build_user_prompt(user_template, case_sections)

        for subject_id in subjects:
            run_index += 1
            subject = registry[subject_id]
            version = resolve_subject_version(subject, args.subject_version)
            subject_version = version["subject_version"]
            litellm_model = litellm_model_for(
                subject_id, subject_version, subject["provider"], args.litellm_model
            )
            track, sampling_kwargs = build_sampling_kwargs(version.get("sampling_policy"))
            run_id = next_run_id(responses_dir, subject_id, case_id)
            label = f"[{run_index}/{total_runs}] {case_id} → {subject_id} ({litellm_model})"
            print(f"{label} ...", end=" ", flush=True)

            raw_text: str | None = None
            metrics: dict[str, Any] = {
                "prompt_tokens": None, "completion_tokens": None,
                "total_tokens": None, "cost_usd": None,
                "price_per_input_token_usd": None,
                "price_per_output_token_usd": None,
                "latency_ms": None,
                "served_model": None,
            }
            status = "fail"
            error_type = ""
            try:
                raw_text, metrics = call_model(
                    litellm_model, system_prompt, user_prompt, args.retries,
                    sampling_kwargs,
                )
                verify_served_model(metrics.get("served_model"), subject_version)
                content = parse_json_from_response(raw_text)
                wrapped = {
                    "case_id": case_id,
                    "benchmark_version": BENCHMARK_VERSION,
                    "subject_id": subject_id,
                    "subject_version": subject_version,
                    "served_model": metrics.get("served_model"),
                    "track": track,
                    "run_id": run_id,
                    "timestamp_utc": utc_iso_now(),
                    **content,
                }
                errors = validate_against(wrapped, response_schema)
                if errors:
                    raise ValueError(
                        "schema validation failed:\n  - " + "\n  - ".join(errors)
                    )
                out_file = save_success(
                    responses_dir, subject_id, case_id, run_id, wrapped
                )
                rel = out_file.relative_to(repo_root)
                tail = format_cost_inline(metrics)
                tail_str = f"  {tail}" if tail else ""
                print(f"{COLOR_GREEN}PASS{COLOR_RESET}{tail_str}  → {rel}")
                passed += 1
                status = "pass"
            except Exception as exc:
                error_type = type(exc).__name__
                err_message = (
                    f"case_id={case_id} subject_id={subject_id} "
                    f"litellm_model={litellm_model} run_id={run_id}\n"
                    f"{error_type}: {exc}"
                )
                err_dir = save_error(
                    responses_dir, subject_id, case_id, run_id, raw_text, err_message
                )
                rel = err_dir.relative_to(repo_root)
                tail = format_cost_inline(metrics)
                tail_str = f"  {tail}" if tail else ""
                print(f"{COLOR_RED}FAIL{COLOR_RESET}{tail_str}  → {rel}/  ({error_type})")
                failed += 1

            batch_rows.append({
                "timestamp_utc": utc_iso_now(),
                "case_id": case_id,
                "subject_id": subject_id,
                "subject_version": subject_version,
                "run_id": run_id,
                "track": track,
                "litellm_model": litellm_model,
                "served_model": metrics.get("served_model") or "",
                "prompt_tokens": metrics.get("prompt_tokens") or "",
                "completion_tokens": metrics.get("completion_tokens") or "",
                "total_tokens": metrics.get("total_tokens") or "",
                "cost_usd": (
                    f"{metrics['cost_usd']:.6f}"
                    if metrics.get("cost_usd") is not None else ""
                ),
                "price_per_input_token_usd": (
                    f"{metrics['price_per_input_token_usd']:.10f}"
                    if metrics.get("price_per_input_token_usd") is not None else ""
                ),
                "price_per_output_token_usd": (
                    f"{metrics['price_per_output_token_usd']:.10f}"
                    if metrics.get("price_per_output_token_usd") is not None else ""
                ),
                "latency_ms": metrics.get("latency_ms") or "",
                "status": status,
                "error_type": error_type,
            })

    print_batch_summary(batch_rows, passed, failed)
    write_batch_log(repo_root, batch_rows)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
