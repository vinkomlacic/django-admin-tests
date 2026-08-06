---
run: run-django-admin-tests-006
work_item: ci-matrix
intent: core-package
mode: confirm
checkpoint: plan
approved_at: pending
---

# Implementation Plan: GitHub Actions CI matrix

## Approach

Add `.github/workflows/ci.yml` with two jobs: a **lint** job (`ruff check`
+ `ruff format --check`, both listed as required gates in
`testing-standards.md`) and a **test** matrix job covering
Python × Django × runner.

Matrix scope was extended beyond the work item's original
"3.10–3.12 × 4.2/5.x" after confirming with the user: that range never
exercises Python 3.14 + Django 6.1, which is what this project is actually
developed on. Support boundaries, verified against PyPI metadata and local
runs:

| Django | Supported Python | In matrix |
|--------|------------------|-----------|
| 4.2 LTS | 3.8 – 3.12 | 3.10, 3.11, 3.12 |
| 5.2 LTS | 3.10 – 3.14 | 3.10 – 3.14 |
| 6.1 (latest) | 3.12+ (`requires_python >=3.12`) | 3.12, 3.13, 3.14 |

That's 11 Python×Django combinations × 2 runners = **22 test cells**,
expressed as a full product with `exclude:` entries for the invalid pairs.

`fail-fast: false` so every cell reports independently, and no
`continue-on-error` anywhere — a regression under one runner must not be
masked by the other passing.

## Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Lint job + 22-cell test matrix, triggered on push and pull_request |

## Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Classifiers currently claim Python 3.10–3.12 and Django 4.2/5.0 only, which contradicts both the new matrix and the local dev environment. Add 3.13/3.14 and Django 5.2/6.0 classifiers. |

## Tests

No new automated tests — the workflow *is* the deliverable. Verification
is by YAML validation, local reproduction of each runner command, and the
matrix-completeness check described below.

## Technical Details

Per-cell install order matters: `pip install -e ".[dev]"` first (which
pulls the newest Django), then `pip install "django==X.Y.*"` to pin the
matrix version — otherwise the editable install silently upgrades Django
back to latest and every cell would test the same version.

Runner selection via `if:` on `matrix.runner`, running either
`pytest tests/` or `python manage.py test tests`.

## Honest verification limits

**This machine only has Python 3.14**, so 18 of the 22 cells cannot be run
locally. What I can and will verify:

- ✅ Python 3.14 + Django 6.1, both runners (the current environment)
- ✅ Python 3.14 + Django 5.2, both runners (already confirmed: 65 passed)
- ✅ Workflow YAML parses, and the matrix expands to exactly the intended
  22 cells (checked programmatically, not by eye)
- ❌ Every Python 3.10–3.13 cell, and all Django 4.2 cells — **unverified
  until CI runs on push**

I will not claim "all matrix cells pass". The AC wording assumes a machine
with multiple Python versions; the honest status is that the workflow is
correct by construction and locally verified where the interpreter allows.

---
This is Checkpoint 1 of Confirm mode.
Approve plan? [Y/n/edit]
