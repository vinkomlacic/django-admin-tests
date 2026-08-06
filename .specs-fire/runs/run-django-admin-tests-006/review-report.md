# Code Review Report

**Run**: run-django-admin-tests-006
**Intent**: core-package
**Reviewed**: 2026-08-07T00:15:00Z
**Files Reviewed**: 2

---

## Summary

| Category | Auto-Fixed | Applied | Skipped |
|----------|------------|---------|---------|
| Code Quality | 0 | 0 | 0 |
| Security | 0 | 1 | 0 |
| Architecture | 0 | 3 | 0 |
| Testing | 0 | 0 | 0 |
| **Total** | **0** | **4** | **0** |

**Tests Status**: Passing in all locally reachable configurations (4 of 22
cells; see test report for the stated limits)

---

## Files Reviewed

- `.github/workflows/ci.yml` (created)
- `pyproject.toml` (modified — classifiers)

---

## Auto-Fixed Issues

None. The workflow isn't Python, so ruff doesn't apply; structural
validation was done programmatically instead.

---

## Applied Suggestions

### 1. [Architecture] Every PR would have run the 22-cell matrix twice

- **File**: `.github/workflows/ci.yml:3`
- **Description**: With bare `push:` and `pull_request:`, a PR opened from
  a branch in this repo triggers both events on every commit — 44 cells
  per push instead of 22.
- **Rationale**: Pure waste at double the matrix size; the standard fix is
  to scope `push` to the default branch, which still satisfies the
  acceptance criterion ("triggers on push and pull_request").
- **Risk Level**: Low (cost/latency, not correctness)
- **Approved**: 2026-08-07T00:12:00Z
- **Diff**: `push: branches: [master]`, with an inline comment explaining
  why the filter exists so it isn't removed as noise later.

### 2. [Architecture] No concurrency control on a 22-cell matrix

- **File**: `.github/workflows/ci.yml:12`
- **Description**: Pushing twice in quick succession left both full matrix
  runs executing.
- **Rationale**: Superseded runs on the same ref are almost never wanted,
  and each one is 22 jobs.
- **Risk Level**: Low
- **Approved**: 2026-08-07T00:12:00Z
- **Diff**: added a `concurrency` group keyed on workflow + ref with
  `cancel-in-progress: true`.

### 3. [Architecture] No pip caching across 22 cells

- **File**: `.github/workflows/ci.yml:27,67`
- **Description**: Every cell re-downloaded Django, pytest, pytest-django
  and ruff from scratch.
- **Rationale**: `setup-python`'s built-in pip cache is a one-line change.
  Cells sharing a Python version share downloaded wheels; since the cache
  holds wheels rather than an installed environment, per-cell Django pins
  are unaffected.
- **Risk Level**: Low
- **Approved**: 2026-08-07T00:12:00Z
- **Diff**: `cache: pip` + `cache-dependency-path: pyproject.toml` on both
  `setup-python` steps.

### 4. [Security] Workflow ran with default (broad) token permissions

- **File**: `.github/workflows/ci.yml:9`
- **Description**: No `permissions:` block, so the job inherited whatever
  the repository default grants.
- **Rationale**: Least privilege — this workflow only needs to read the
  checkout. Matches `constitution.md`'s security posture.
- **Risk Level**: Low (defense in depth)
- **Approved**: 2026-08-07T00:12:00Z
- **Diff**: added top-level `permissions: contents: read`.

---

## Skipped Suggestions

No suggestions were skipped.

---

## Project Tooling Used

`actionlint` is not installable in this environment, so workflow
validation was done programmatically instead of by a dedicated linter:
YAML parse, trigger/permission/concurrency inspection, and — the useful
part — **re-deriving the valid Python×Django cell set independently from
the support boundaries** and comparing it to what the `exclude:` list
actually produces. Copying the exclusions into the assertion would have
made the check incapable of catching a wrong exclusion; deriving them
separately means it can.

Re-validated after all four changes: still 22 cells, boundaries still
match, `fail-fast: false` intact, no `continue-on-error`.

### Note for `packaging-release-readiness`

`pyproject.toml` classifiers were corrected here (they claimed Python
3.10–3.12 / Django 4.2–5.0 while the project runs on 3.14 / Django 6.1).
The remaining metadata gaps — project URLs, keywords, and a README that
still contains only a title — belong to the final work item, which should
also add a CI status badge now that a workflow exists.

---

## Standards Referenced

- `.specs-fire/standards/constitution.md`
- `.specs-fire/standards/tech-stack.md`
- `.specs-fire/standards/testing-standards.md`
