#!/usr/bin/env python3
"""Universal governance checks — the stack-agnostic base gate (run via pre-commit).

These are the *language-agnostic* governance rules every repo of this family enforces,
implemented in pure stdlib so they run under any stack's toolchain (the cross-stack hook
runner `pre-commit` provides the Python). A LANGUAGE stack overlay adds its own structure-lint
(member/typing/service checks) in its native mechanism on top of this — those are NOT here.

Lifted from the four universal checks in the reference `tests/test_structure.py`:
  1. every `.github/workflows/` Action is SHA-pinned (supply-chain mandate; see docs/adr/0003),
  2. LICENSE is the verbatim full Apache-2.0 text (not swapped or truncated),
  3. root Markdown is limited to the OSS-furniture allowlist; everything else lives under docs/,
  4. every docs/ knowledge artefact carries enum-valid YAML frontmatter.

Exit 0 if clean, 1 (with an enumerated report) on any violation. Fail-closed: a check that
cannot read its inputs reports a problem rather than passing vacuously.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Root furniture Markdown allowed at the repo ROOT (everything else .md must live under docs/).
ROOT_MD_ALLOWLIST: frozenset[str] = frozenset(
    {
        "README.md",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "AGENTS.md",
        "AGENTS.local.md",
        "CLAUDE.md",
    }
)

# Frontmatter contract for docs/ knowledge artefacts (governance-standards L2 header).
FRONTMATTER_TYPES: frozenset[str] = frozenset({"SKILL", "WORKFLOW", "LESSON", "ADR", "REFERENCE"})
FRONTMATTER_STATUS: frozenset[str] = frozenset({"EXPERIMENTAL", "VERIFIED", "DEPRECATED"})

# A SHA-pinned Action ref ends in a 40-char hex commit; docker:// actions pin by image digest.
# `uses:` is matched ANYWHERE on the line so a flow-style `[{ uses: x@tag }]` cannot evade it.
_SHA_PIN = re.compile(r"@[0-9a-f]{40}$")
_DIGEST_PIN = re.compile(r"@sha256:[0-9a-f]{64}$")
_USES_REF = re.compile(r"\buses:\s*(?P<ref>[^\s#]+)")

# Genuine noise skipped at any depth.
_NOISE_DIRS = {".git", ".venv", "venv", "__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache"}


def _drop_git_ignored(paths: list[Path]) -> list[Path]:
    """Drop git-ignored paths so the gate enforces only tracked + untracked-not-ignored files.
    A deliberately git-ignored path (e.g. a local-only docs/sessions/ handoff dir) is the
    author's "keep this out of the repo" choice. No-op outside a git work tree (fail-closed:
    every path kept), so a non-git checkout still lints fully."""
    if not paths:
        return paths
    rels = {p: p.relative_to(REPO_ROOT).as_posix() for p in paths}
    try:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", "--stdin", "-z"],
            input="".join(f"{rel}\0" for rel in rels.values()),
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return paths
    ignored = {entry for entry in proc.stdout.split("\0") if entry}
    return [p for p, rel in rels.items() if rel not in ignored]


def _iter_md() -> list[Path]:
    """Every .md under the repo, skipping genuine noise dirs and git-ignored paths."""
    out: list[Path] = []
    for p in REPO_ROOT.rglob("*.md"):
        if any(part in _NOISE_DIRS for part in p.relative_to(REPO_ROOT).parts):
            continue
        out.append(p)
    return _drop_git_ignored(out)


def _read_frontmatter(md: Path) -> dict[str, str] | None:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip("'\"")
    return fm


def check_actions_sha_pinned() -> list[str]:
    """Every external `uses:` in .github/workflows/ pins a 40-hex SHA (or @sha256: digest)."""
    wf_dir = REPO_ROOT / ".github" / "workflows"
    if not wf_dir.is_dir():
        return []  # no workflows yet — vacuously clean
    problems: list[str] = []
    for wf in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        for line in wf.read_text(encoding="utf-8").splitlines():
            for m in _USES_REF.finditer(line):
                ref = m.group("ref").strip("\"'")
                if ref.startswith("./"):
                    continue  # local composite action — no external ref to pin
                if ref.startswith("docker://"):
                    if not _DIGEST_PIN.search(ref):
                        problems.append(f"{wf.name}: {ref} (docker:// needs @sha256:<digest>)")
                    continue
                if not _SHA_PIN.search(ref):
                    problems.append(f"{wf.name}: {ref} (Action not SHA-pinned)")
    return problems


def check_license_verbatim_apache() -> list[str]:
    """LICENSE is the full verbatim Apache-2.0 text — not swapped, stubbed, or truncated."""
    lic = REPO_ROOT / "LICENSE"
    if not lic.is_file():
        return ["LICENSE: missing"]
    text = lic.read_text(encoding="utf-8")
    problems: list[str] = []
    for marker in ("Apache License", "Version 2.0", "TERMS AND CONDITIONS"):
        if marker not in text:
            problems.append(f"LICENSE: missing Apache-2.0 marker {marker!r} (not verbatim)")
    return problems


def check_root_md_allowlist() -> list[str]:
    """Root .md limited to the furniture allowlist; all other .md under docs/ or .github/."""
    problems: list[str] = []
    for md in _iter_md():
        parts = md.relative_to(REPO_ROOT).parts
        if len(parts) == 1:
            if parts[0] not in ROOT_MD_ALLOWLIST:
                problems.append(f"{parts[0]}: Markdown not in the root allowlist (move under docs/)")
        elif parts[0] in {"docs", ".github"}:
            continue
        else:
            problems.append(f"{'/'.join(parts)}: Markdown outside root-allowlist / docs / .github")
    return problems


def check_docs_frontmatter() -> list[str]:
    """Every docs/ knowledge artefact carries enum-valid frontmatter (id/gist/type/status)."""
    docs = REPO_ROOT / "docs"
    if not docs.is_dir():
        return []
    problems: list[str] = []
    for md in _drop_git_ignored(list(docs.rglob("*.md"))):
        if md.name.upper() == "README.MD":
            continue
        rel = "/".join(md.relative_to(REPO_ROOT).parts)
        fm = _read_frontmatter(md)
        if fm is None:
            problems.append(f"{rel}: no YAML frontmatter")
            continue
        for key in ("id", "gist"):
            if not fm.get(key):
                problems.append(f"{rel}: missing required frontmatter key {key!r}")
        if fm.get("type") not in FRONTMATTER_TYPES:
            problems.append(f"{rel}: type={fm.get('type')!r} not in {sorted(FRONTMATTER_TYPES)}")
        if fm.get("status") not in FRONTMATTER_STATUS:
            problems.append(f"{rel}: status={fm.get('status')!r} not in {sorted(FRONTMATTER_STATUS)}")
        if fm.get("type") == "ADR" and md.relative_to(REPO_ROOT).parts[:2] != ("docs", "adr"):
            problems.append(f"{rel}: ADR-typed doc must live under docs/adr/")
    return problems


def main() -> int:
    checks = (
        ("Actions SHA-pinned", check_actions_sha_pinned),
        ("LICENSE verbatim Apache-2.0", check_license_verbatim_apache),
        ("root Markdown allowlist", check_root_md_allowlist),
        ("docs frontmatter enum", check_docs_frontmatter),
    )
    failed = False
    for name, fn in checks:
        problems = fn()
        if problems:
            failed = True
            print(f"[governance] {name}: FAIL")
            for p in problems:
                print(f"  - {p}")
    if failed:
        print("\n[governance] universal governance checks FAILED", file=sys.stderr)
        return 1
    print("[governance] universal governance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
