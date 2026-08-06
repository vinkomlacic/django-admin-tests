# Code Review Report

**Run**: run-django-admin-tests-007
**Intent**: core-package
**Reviewed**: 2026-08-07T01:10:00Z
**Files Reviewed**: 7

---

## Summary

| Category | Auto-Fixed | Applied | Skipped |
|----------|------------|---------|---------|
| Code Quality | 0 | 0 | 0 |
| Security | 0 | 1 | 0 |
| Architecture | 0 | 1 | 0 |
| Testing | 0 | 2 | 0 |
| **Total** | **0** | **4** | **0** |

**Tests Status**: Passing (79 passed, 1 skipped by design, 20 subtests, 99% coverage)

---

## Files Reviewed

- `README.md` (rewritten)
- `CHANGELOG.md` (created)
- `LICENSE` (created)
- `pyproject.toml` (modified)
- `.github/workflows/ci.yml` (modified — coverage job)
- `tests/test_admin_smoke.py`, `tests/test_instantiation.py`, `tests/test_pytest_plugin.py` (new tests)

---

## Applied Suggestions

### 1. [Security] Sdist published internal tooling and developer paths

- **File**: `pyproject.toml`
- **Description**: `hatchling`'s `packages` setting scopes the wheel only.
  The sdist included `.claude/settings.local.json` (absolute developer
  paths), the entire `.specsmd/` tooling, and every internal `.specs-fire/`
  planning document — all destined for PyPI.
- **Rationale**: Publishing is irreversible; PyPI artifacts can't be
  quietly recalled. No credentials were exposed, but internal planning
  notes and a developer's home directory path have no business in a
  distribution.
- **Risk Level**: Medium
- **Approved**: 2026-08-07T00:55:00Z
- **Diff**: explicit `[tool.hatch.build.targets.sdist] include = [...]`
  allowlist. Sdist went from 136K to 24K.

### 2. [Testing] Coverage was asserted, never measured — and was wrong

- **File**: `pyproject.toml`, plus new tests across three test modules
- **Description**: Runs 001–006 each reported "100% coverage" without
  running a coverage tool. Actual figure was 92%, with genuinely untested
  paths including `user_factory` — a public API this run's README
  documents. Separately, `pytest --cov` understates this package by ~13
  points because it's imported via its own `pytest11` entry point before
  pytest-cov begins tracing.
- **Rationale**: An unmeasured coverage number in a test report is worse
  than no number: it looks like evidence. `testing-standards.md` makes
  coverage a CI-blocking gate, which had never actually been enforced.
- **Risk Level**: High (false assurance across six reports)
- **Approved**: 2026-08-07T00:50:00Z
- **Diff**: added tests closing every real gap; pinned
  `[tool.coverage.run]`/`[tool.coverage.report]` with `fail_under = 90`
  and a comment explaining the `coverage run -m pytest` requirement; added
  a `coverage` job to CI so the gate is enforced rather than assumed.

### 3. [Testing] The clean-install check imported from the source tree

- **File**: verification procedure (not a committed file)
- **Description**: Running `python -c "import django_admin_tests"` from
  the project directory resolves the source tree, because Python puts the
  cwd on `sys.path`. The check passed while proving nothing about the
  built artifact.
- **Rationale**: The entire point of the check is to validate the *wheel*.
- **Risk Level**: Medium (false assurance)
- **Approved**: 2026-08-07T00:58:00Z
- **Diff**: re-ran from outside the source tree with an assertion that the
  module resolves under `site-packages`.

### 4. [Architecture] README claimed capabilities without stating limits

- **File**: `README.md`
- **Description**: A first draft would have presented the pytest plugin as
  zero-config and omitted known rough edges.
- **Rationale**: The plugin is opt-in by deliberate design (run-005), and
  three real limitations surfaced during development: models that can't be
  auto-instantiated are skipped rather than failed, `AUTH_USER_MODEL`
  support is `user_factory`-only, and importing `AdminSmokeTestCase` by
  name causes discovery to collect the base class too. Users hit these on
  day one; better they read them than discover them.
- **Risk Level**: Low (documentation honesty)
- **Approved**: 2026-08-07T00:45:00Z
- **Diff**: "Known limitations" section, an inline note on the import
  gotcha, and the opt-in flag shown in the plugin section rather than
  buried.

---

## Skipped Suggestions

No suggestions were skipped.

---

## Project Tooling Used

- **ruff**: `ruff check .` and `ruff format --check .` both pass
- **twine**: `twine check` PASSED on both sdist and wheel
- **coverage**: 99%, above the 90% gate (see correction above)
- **build**: sdist + wheel; both installed into clean venvs and imported

---

## Note for the user before publishing

`version` remains `0.1.0.dev0`. Choosing the release number is a product
decision, not something to slip into a packaging task — bump it
deliberately when you're ready to tag. The `CHANGELOG.md` entry is
currently under `[Unreleased]` and should be retitled to match.

---

## Standards Referenced

- `.specs-fire/standards/constitution.md`
- `.specs-fire/standards/tech-stack.md`
- `.specs-fire/standards/testing-standards.md`
- `.specs-fire/standards/coding-standards.md`
