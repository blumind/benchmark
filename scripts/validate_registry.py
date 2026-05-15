#!/usr/bin/env python3
"""Validate the subject registry against registry.schema.json.

Default target: subjects/registry.yaml at the repo root.

Usage:
    python scripts/validate_registry.py                  # default location
    python scripts/validate_registry.py path/to/file.yaml

Cross-file invariants (beyond the schema):
    - subject_id is unique across the 'subjects' array.
    - subject_version is unique within each subject's 'versions' array.
    - For LLM subjects, subject_version must be a real pinned snapshot:
      it cannot equal subject_id (which is the unpinned alias), and it
      must start with subject_id as a prefix. This blocks the alias trap
      that v1.0 hit once (calling 'openai/gpt-5' instead of a snapshot).
    - For LLM subjects, every version MUST declare a sampling_policy
      block. This is the binding declaration of which v1.0 track the
      version belongs to (classic = temperature=0; reasoning = provider
      defaults + reasoning_effort). See docs/run_evaluation_design.md
      § Sampling policy.

Exit codes: 0 (valid) or 1 (failed).
"""

from __future__ import annotations

import sys
from pathlib import Path

from _validator_common import (
    find_repo_root,
    load_schema,
    load_data,
    validate_against,
    report_file,
    summary,
)


def cross_check(data: dict) -> list[str]:
    extra = []
    subjects = data.get("subjects", []) or []

    ids = [s.get("subject_id") for s in subjects]
    seen: dict[str, list[int]] = {}
    for i, sid in enumerate(ids):
        seen.setdefault(sid, []).append(i)
    duplicates = {sid: idxs for sid, idxs in seen.items() if len(idxs) > 1}
    if duplicates:
        extra.append(f"subjects: duplicate subject_id(s): {duplicates}")

    for s in subjects:
        sid = s.get("subject_id", "<unknown>")
        kind = s.get("kind")
        versions = [v.get("subject_version") for v in s.get("versions", []) or []]
        if len(versions) != len(set(versions)):
            extra.append(
                f"subjects/{sid}/versions: duplicate subject_version(s) "
                f"in {versions}"
            )

        if kind == "llm":
            for v in s.get("versions", []) or []:
                sv = v.get("subject_version")
                pins_id = bool(v.get("provider_pins_id", False))
                policy = v.get("sampling_policy")
                if not isinstance(policy, dict) or not policy.get("kind"):
                    extra.append(
                        f"subjects/{sid}/versions[{sv!r}]: missing required "
                        "'sampling_policy' block. Every kind=llm version "
                        "must declare {kind: classic} or {kind: reasoning, "
                        "reasoning_effort: ...} so the runner knows which "
                        "evaluation track to use. See "
                        "docs/run_evaluation_design.md § Sampling policy."
                    )
                else:
                    pk = policy.get("kind")
                    if pk == "classic" and "reasoning_effort" in policy:
                        extra.append(
                            f"subjects/{sid}/versions[{sv!r}]: "
                            "sampling_policy.kind='classic' forbids "
                            "'reasoning_effort'. Either switch to "
                            "kind='reasoning' or drop the knob."
                        )
                if not isinstance(sv, str) or not sv:
                    continue
                if sv == sid and not pins_id:
                    extra.append(
                        f"subjects/{sid}/versions: subject_version {sv!r} "
                        "equals subject_id; LLM versions must be a pinned "
                        "snapshot, never an unpinned alias. If the provider "
                        "pins this exact id (e.g. Anthropic Opus 4.6+), set "
                        "'provider_pins_id: true' on this version entry."
                    )
                elif not _family_matches(sv, sid):
                    extra.append(
                        f"subjects/{sid}/versions: subject_version {sv!r} "
                        f"does not share a family prefix with subject_id "
                        f"{sid!r}. Expected the first token of the "
                        "subject_id (e.g. 'mistral', 'gpt', 'claude') to "
                        "appear in the snapshot id to catch gross mismatches "
                        "like pinning a Claude snapshot under a GPT subject."
                    )

    return extra


def _family_matches(version: str, subject_id: str) -> bool:
    """Loose sanity check: the model family token must appear in the snapshot.

    Provider naming conventions vary too much for a strict startswith
    check (e.g. subject_id 'mistral-small-3' vs subject_version
    'mistral-small-2603'; subject_id 'gpt-3-5-turbo' vs subject_version
    'gpt-3.5-turbo-0125'). The runtime served_model verification in
    run_evaluation.py is the binding gate against alias drift; this
    check only catches catastrophic registry mistakes (e.g. pinning a
    Claude snapshot under a GPT subject_id).
    """
    family = subject_id.split("-", 1)[0].lower()
    return family in version.lower().replace(".", "-").replace("_", "-")


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    schema = load_schema(repo_root, "registry")

    target = (
        Path(argv[1]) if len(argv) > 1 else repo_root / "subjects" / "registry.yaml"
    )

    if not target.is_file():
        print(f"ERROR: file not found: {target}", file=sys.stderr)
        return 2

    try:
        data = load_data(target)
        errors = validate_against(data, schema) + cross_check(data)
    except Exception as exc:
        errors = [f"<load>: {exc}"]

    valid = report_file(target, errors)
    return summary(1 if valid else 0, 0 if valid else 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
