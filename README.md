# template-governance-base

A [Copier](https://copier.readthedocs.io/) template that renders the **stack-agnostic governance
kernel** for a repository: the standard OSS furniture (licence, code of conduct, contributing,
security policy, issue/PR templates), agent-instruction files, and a **language-agnostic
enforcement layer** (`pre-commit`) that holds universal governance rules — Actions SHA-pinning,
verbatim licence, root-Markdown allowlist, and `docs/` frontmatter — without assuming any
particular language toolchain.

It is the **base** of a template family. Per-stack overlays (e.g. `template-py-uv-workspace`)
compose on top of it and add the language-specific structure-lint and tooling. Apply order:
`template-governance-base` → stack overlay → capability overlay.

## Usage

```bash
# Render a new repo from the base.
uvx copier copy gh:Astenuprax/template-governance-base my-new-repo

# Later, pull governance updates into an existing consumer.
cd my-new-repo
uvx copier update -a .copier-answers.base.yml
```

The render writes a `.copier-answers.base.yml` linkage file — keep it; it is what `copier update`
uses to propagate later governance changes via 3-way merge.

## What this base does NOT ship

No `pyproject.toml`, no `tests/`, no language structure-lint. Those are the language overlay's
job — pytest is a Python mechanism, and the base must stay stack-agnostic. The universal governance
checks the base *does* enforce run through `pre-commit` (the cross-stack hook runner), not pytest.

## Governance

This template propagates the `repo-structure-standard`, `repo-hygiene`, and `governance-standards`
conventions (referenced by name; not restated here).

## License

Apache-2.0. See `LICENSE`.

---

Maintainer: Phillip Anderson | Integrate-IT Australia
