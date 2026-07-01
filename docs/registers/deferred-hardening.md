---
id: REF-DEFERRED-HARDENING-001
type: REFERENCE
status: EXPERIMENTAL
gist: Durable register of consciously-deferred hardening and known gaps for template-governance-base itself.
---

# Deferred-Hardening Register

The single durable home for **consciously-deferred** work and known gaps in `template-governance-base`
itself (the project's own dev backlog, not the artifacts it renders into consumer repos).

## Open

| # | Item | Why deferred | Trigger to revisit |
|---|------|--------------|--------------------|
| D-1 | **`governance_checks.py::ROOT_MD_ALLOWLIST` does not include `ROADMAP.md`.** A rendered repo (normal, non-AI-monorepo archetype) that creates a root `ROADMAP.md` — the canonical lazy strategic-arc artifact per `project-planning-artifacts` — will fail its own rendered pre-commit gate on the root-md-allowlist check. Found while building the `is_ai_monorepo` planning-artifact carve-out (Workstream 2 of `plans/vast-tumbling-hamming.md`). | `ROADMAP.md` is a **lazy** artifact — this overlay does not render it, so the gap doesn't bite until a downstream repo creates one. Not in scope for the eager-skeleton build. | Any rendered repo creates a root `ROADMAP.md` and hits the allowlist failure — add `ROADMAP.md` to `ROOT_MD_ALLOWLIST`, or (AI-monorepo archetype) confirm the `docs/planning/ROADMAP.md` path is already covered by the `docs/**` frontmatter gate instead. |

## Closed

<!-- Move an item here with a completion date (dd/mm/yyyy) and the proof when it ships. -->

| # | Item | Closed | Proof |
|---|------|--------|-------|

---

Author: Phillip Anderson | Integrate-IT Australia
