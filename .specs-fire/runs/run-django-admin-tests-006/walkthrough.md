---
run: run-django-admin-tests-006
work_item: ci-matrix
intent: core-package
generated: 2026-08-07T00:20:00Z
mode: confirm
---

# Implementation Walkthrough: GitHub Actions CI matrix

## Summary

Added `.github/workflows/ci.yml`: a lint job plus a 22-cell test matrix
covering Python 3.10–3.14 × Django 4.2/5.2/6.1 × both runners, restricted
to valid combinations. Also corrected `pyproject.toml` classifiers, which
claimed Python 3.10–3.12 and Django 4.2–5.0 while the project is actually
developed on Python 3.14 with Django 6.1.

## Structure Overview

Two jobs. `lint` runs `ruff check` and `ruff format --check` on a single
Python version — both are listed as required gates in
`testing-standards.md`. `test` is the matrix: a full Python × Django ×
runner product with `exclude:` entries removing combinations Django
doesn't support, giving 22 cells that each install the package and run the
dogfood suite under either `pytest` or `manage.py test`.

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Lint gate + 22-cell matrix, on push (master) and pull_request |

### Modified

| File | Changes |
|------|---------|
| `pyproject.toml` | Classifiers: added Python 3.13/3.14 and Django 5.2/6.0; dropped the stale Django 5.0 claim |

## Key Implementation Details

### 1. The specified matrix didn't cover the environment we develop on

The work item asked for Python 3.10–3.12 × Django 4.2/5.x. This project
runs on Python 3.14 + Django 6.1, so that matrix would have left the actual
development environment completely untested while the classifiers
advertised versions nobody had exercised. Raised with the user, who chose
to extend the matrix; support boundaries were then taken from PyPI metadata
rather than memory (Django 6.1 declares `requires_python >=3.12`).

### 2. Install order would have silently invalidated the entire matrix

`pip install -e ".[dev]"` resolves Django to the newest release. Pinning
the matrix version *before* the editable install therefore gets
overwritten, and all 22 cells would test one Django version while
appearing to test three — a green matrix proving nothing. The workflow
pins after, and a clean-venv local run confirmed the pin sticks (resolved
Django 5.2.17, not 6.1). Commented inline so the ordering isn't
"simplified" later.

### 3. Validating the matrix by re-deriving it, not by re-reading it

Checking the `exclude:` list by eye — or asserting against the same list —
can't catch a wrong exclusion. Instead the validation computes the valid
Python×Django set independently from the support boundaries and compares
it against what the workflow's exclusions actually produce. That's what
makes "22 cells" a verified claim rather than a count.

### 4. CI hygiene for a 22-cell matrix

Four issues found in review, all cheap to fix and all more consequential at
22 cells than they would be at two: PRs from in-repo branches ran the whole
matrix twice (fixed by scoping `push` to master), no concurrency
cancellation, no pip caching, and default-broad token permissions.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Matrix scope | Extended to Python 3.10–3.14 × Django 4.2/5.2/6.1 | The original range never exercised the dev environment; confirmed with the user |
| Support boundaries | Read from PyPI metadata | Django 6.1's `requires_python >=3.12` is a fact worth checking rather than assuming |
| `push` trigger | Scoped to `master` | Avoids running 44 cells per PR commit; still satisfies "triggers on push" |
| Claiming full-matrix success | Explicitly not claimed | 18 cells are unrunnable on this machine; see below |

## Deviations from Plan

None. The four CI-hygiene improvements were found during the review phase
rather than planned, but they don't change the deliverable's shape.

## Dependencies Added

None.

## How to Verify

1. **Workflow structure and cell count**

   ```bash
   source .venv/bin/activate
   python -c "
   import itertools, yaml
   wf = yaml.safe_load(open('.github/workflows/ci.yml'))
   m = wf['jobs']['test']['strategy']['matrix']
   combos = list(itertools.product(m['python-version'], m['django-version'], m['runner']))
   ex = m.get('exclude', [])
   keys = ('python-version','django-version','runner')
   kept = [c for c in combos if not any(all(dict(zip(keys,c))[k]==v for k,v in e.items()) for e in ex)]
   print(len(kept), 'cells')"
   ```

   Expected: `22 cells`.

2. **The two runner commands, as CI invokes them**

   ```bash
   pytest tests/
   python manage.py test tests
   ```

   Expected: `65 passed, 1 skipped` and `Ran 3 tests ... OK (skipped=1)`.

3. **The full matrix** — push the branch. This is the only way to verify
   the remaining 18 cells.

## Test Coverage

- Tests added: 0 (the workflow is the deliverable; it runs the existing 65-test suite)
- Coverage: unchanged at 100% of shipped modules
- Status: passing in all 4 locally reachable cells

## Ready for Review

- [x] Workflow validated structurally and by independent re-derivation
- [x] Locally reachable cells pass
- [x] No critical issues
- [ ] Documentation updated (README/badge — `packaging-release-readiness`)
- [x] Developer notes captured

## Developer Notes

- **18 of 22 cells are unverified.** This machine has only Python 3.14, so
  every Python 3.10–3.13 cell and every Django 4.2 cell will run for the
  first time on push. Django 4.2 in particular cannot be tested here at
  all — it supports Python ≤3.12, so the combination is invalid on this
  interpreter, and an attempted run failed for that reason rather than
  anything about this codebase. If Django 4.2 cells fail in CI, that's new
  information, not a known-broken state.
- `actionlint` wasn't installable here. If it's available in your
  environment, running it over the workflow is worthwhile — the
  programmatic checks cover structure and matrix correctness but not
  action-specific schema mistakes.
- The pip cache is keyed on `pyproject.toml`, so changing dependencies
  invalidates it automatically; no manual cache busting needed.

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-006*
