#!/usr/bin/env python3
"""Minimal Operator Lock-In docs audit (stdlib-only).

Checks for the presence of expected Operator Lock-In roles without
inventing fiction: reports what exists, marks the rest TODO/missing.

Expected roles:
  - AGENTS.md router
  - filetree spatial map
  - CONTEXT.md / MEMORY.md / NOTEPAD.md / TASK.md / PLAN.md continuity set
  - SPEC.md normative spec (if present)
  - schemas/v1/ validation truth, examples/ usage truth, tools/ runnable truth

CLI:
  python3 tools/operator_docs_audit.py [--root PATH]

Exit code is always 0; this tool reports, it does not fail the build.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


EXPECTED_FILES: list[tuple[str, str]] = [
    ("AGENTS.md", "AGENTS router (entry points, authority map)"),
    ("filetree.md", "spatial map (tree + ownership, NOT a router)"),
    ("SPEC.md", "normative spec (if present; else Research.md is evidence)"),
    ("CONTEXT.md", "continuity: active context handoff"),
    ("MEMORY.md", "continuity: durable decisions"),
    ("NOTEPAD.md", "continuity: transient working notes"),
    ("TASK.md", "continuity: task packet"),
    ("PLAN.md", "continuity: execution plan"),
    ("Somnus Markdown Metadata Standard Research.md", "evidence source of truth (read-only)"),
]

EXPECTED_DIRS: list[tuple[str, str]] = [
    ("schemas/v1", "validation truth (core.json + profiles/)"),
    ("examples", "usage truth (specification/benchmark/submatter examples)"),
    ("tools", "runnable truth (validate.py, operator_docs_audit.py)"),
]


def audit(root: Path) -> int:
    print(f"Operator docs audit: {root}")
    missing: list[str] = []
    present: list[str] = []

    for name, role in EXPECTED_FILES:
        p = root / name
        if p.is_file():
            try:
                size = p.stat().st_size
            except OSError:
                size = -1
            print(f"PRESENT {name} ({size} bytes) -- {role}")
            present.append(name)
        else:
            print(f"MISSING {name} -- {role} -- TODO: create only if needed, do not invent content")
            missing.append(name)

    for name, role in EXPECTED_DIRS:
        p = root / name
        if p.is_dir():
            try:
                count = sum(1 for _ in p.rglob("*") if _.is_file())
            except OSError:
                count = -1
            print(f"PRESENT {name}/ ({count} file(s)) -- {role}")
            present.append(name)
        else:
            print(f"MISSING {name}/ -- {role} -- TODO")
            missing.append(name)

    # Do not parse content deeply; only report existence to avoid fiction.
    print(f"Summary: {len(present)} present, {len(missing)} missing")
    if missing:
        print("TODO (missing-only, no fiction): " + ", ".join(missing))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit Operator Lock-In docs presence.")
    ap.add_argument("--root", default=".", help="Workspace root to audit (default: cwd)")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR root is not a directory: {root}", file=sys.stderr)
        return 2
    return audit(root)


if __name__ == "__main__":
    sys.exit(main())
