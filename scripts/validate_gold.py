#!/usr/bin/env python3
"""Validate gold Markdown files against gold.schema.json.

Each gold file is expected at golds/v1.0/RO-<FAMILY>-<NNN>_gold.md and
embeds exactly one ```json``` code block. This validator extracts that
block, parses it as JSON, validates against the schema, and runs cross-file
invariants.

Usage:
    python scripts/validate_gold.py                   # validate all under golds/
    python scripts/validate_gold.py path/to/file.md   # validate one
    python scripts/validate_gold.py path/to/dir       # validate dir tree

Cross-file invariants (beyond the schema):
    - The filename stem (minus the '_gold' suffix) matches the case_id.
    - The 'family' field matches the family segment of case_id.
    - rubric_floor < rubric_ceiling.

Exit codes: 0 (all valid) or 1 (any failed).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _validator_common import (
    find_repo_root,
    load_schema,
    validate_against,
    report_file,
    summary,
)


JSON_BLOCK_RE = re.compile(r"^```json\s*\n(.*?)^```", re.DOTALL | re.MULTILINE)


def extract_json_block(md_text: str) -> str:
    matches = JSON_BLOCK_RE.findall(md_text)
    if not matches:
        raise ValueError("no ```json``` code block found in the gold markdown")
    if len(matches) > 1:
        raise ValueError(
            f"expected exactly one ```json``` code block, found {len(matches)}"
        )
    return matches[0]


def cross_check(data: dict, path: Path) -> list[str]:
    extra = []
    expected_case = path.stem.removesuffix("_gold")
    if data.get("case_id") != expected_case:
        extra.append(
            f"<filename>: case_id in JSON ({data.get('case_id')!r}) "
            f"does not match filename ({expected_case!r})"
        )
    case_id = data.get("case_id", "")
    parts = case_id.split("-")
    if len(parts) >= 2:
        family_segment = parts[1]
        if data.get("family") != family_segment:
            extra.append(
                f"family/case_id: family ({data.get('family')!r}) does not "
                f"match the family segment of case_id ({family_segment!r})"
            )
    floor = data.get("rubric_floor", 0)
    ceiling = data.get("rubric_ceiling", 12)
    if isinstance(floor, int) and isinstance(ceiling, int) and floor >= ceiling:
        extra.append(
            f"rubric_floor/rubric_ceiling: rubric_floor ({floor}) must be "
            f"strictly less than rubric_ceiling ({ceiling})"
        )
    return extra


def main(argv: list[str]) -> int:
    repo_root = find_repo_root()
    schema = load_schema(repo_root, "gold")

    explicit = len(argv) > 1
    target = Path(argv[1]) if explicit else repo_root / "golds"

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("*_gold.md"))
    elif not explicit:
        print(f"Default target {target} does not exist; nothing to validate.")
        print("(Golds typically live in a separate private repository.)")
        return 0
    else:
        print(f"ERROR: path not found: {target}", file=sys.stderr)
        return 2

    passed = failed = 0
    for f in files:
        try:
            md = f.read_text()
            json_text = extract_json_block(md)
            data = json.loads(json_text)
            errors = validate_against(data, schema) + cross_check(data, f)
        except Exception as exc:
            errors = [f"<extract/parse>: {exc}"]
        if report_file(f, errors):
            passed += 1
        else:
            failed += 1

    return summary(passed, failed)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
