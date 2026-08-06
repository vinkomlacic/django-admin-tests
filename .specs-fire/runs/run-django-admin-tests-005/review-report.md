# Code Review Report

**Run**: run-django-admin-tests-005
**Intent**: core-package
**Reviewed**: 2026-08-06T22:20:00Z
**Files Reviewed**: 7

---

## Summary

| Category | Auto-Fixed | Applied | Skipped |
|----------|------------|---------|---------|
| Code Quality | 0 | 0 | 0 |
| Security | 0 | 0 | 0 |
| Architecture | 0 | 2 | 0 |
| Testing | 0 | 1 | 0 |
| **Total** | **0** | **3** | **0** |

**Tests Status**: Passing (65 passed, 1 skipped by design, 20 subtests)

---

## Files Reviewed

- `django_admin_tests/pytest_plugin.py` (source, rewritten from stub)
- `django_admin_tests/settings.py` (source, created)
- `django_admin_tests/testcases.py` (source, modified)
- `pyproject.toml` (config, modified)
- `tests/conftest.py` (test, modified)
- `tests/test_settings.py` (test, created)
- `tests/test_pytest_plugin.py` (test, created)

---

## Auto-Fixed Issues

No auto-fixes needed; `ruff format`/`ruff check` were clean on first pass
for the new modules.

---

## Applied Suggestions

### 1. [Architecture] Dedup check could false-positive on a host project's own `testcases.py`

- **File**: `django_admin_tests/pytest_plugin.py:56`
- **Description**: The "already collected" guard compared
  `item.nodeid.startswith("testcases.py")`. Any host project with its own
  top-level `testcases.py` would match, silently suppressing injection —
  a confusing, hard-to-diagnose no-op.
- **Rationale**: `testcases.py` is a plausible filename in a Django
  project; a plugin must not depend on the host not using it.
- **Risk Level**: Medium (silent feature failure, not a crash)
- **Approved**: 2026-08-06T22:15:00Z
- **Diff**: compare resolved `Path` objects (`item.path == smoke_path`)
  instead of nodeid string prefixes.

### 2. [Architecture] Missing graceful-degradation guard promised in the plan

- **File**: `django_admin_tests/pytest_plugin.py:60`
- **Description**: The approved plan committed to degrading gracefully so
  a failure inside injection can't abort collection of the host project's
  unrelated tests; the first implementation let exceptions propagate.
- **Rationale**: An opt-in convenience feature should not be able to take
  down someone's whole test session.
- **Risk Level**: Medium
- **Approved**: 2026-08-06T22:15:00Z
- **Diff**: wrapped injection in `try/except`, emitting a warning naming
  the failure and how to disable the feature.

### 3. [Testing] Guard test asserted something the guard can't actually do

- **File**: `tests/test_pytest_plugin.py`
- **Description**: The first version of the guard test gave the host
  project a broken `admin.py` and expected the plugin to shrug it off.
  Running it revealed that a broken admin raises inside `django.setup()`
  during pytest-django's configure step — *before* our hook ever runs — so
  the whole session dies regardless of the guard. The test was asserting
  behavior the code cannot provide.
- **Rationale**: Better to test what the guard genuinely protects (a
  failure inside our own collection step) than to keep a test whose name
  implies a stronger guarantee than exists.
- **Risk Level**: Low (test-only), but the misleading claim mattered
- **Approved**: 2026-08-06T22:18:00Z
- **Diff**: replaced with a focused unit test that makes
  `_collect_smoke_items` raise and asserts the hook warns, leaves the
  host's item list untouched, and doesn't propagate. The docstring now
  states explicitly that broken-admin-at-import is Django's failure to
  report, not ours to swallow.

---

## Skipped Suggestions

No suggestions were skipped.

---

## Project Tooling Used

- **ruff (lint)**: `pyproject.toml` — `ruff check .` passes
- **ruff (format)**: `pyproject.toml` — `ruff format --check .` passes

Manual review against `review-categories.md`:

- **Security**: settings accessors validate types and raise
  `ImproperlyConfigured` with actionable messages rather than failing
  obscurely later. The generated test project's `SECRET_KEY` is a
  test-only literal in a temp directory.
- **Architecture**: the pytest import stays confined to
  `pytest_plugin.py`; `settings.py` imports only `django.conf`/
  `django.core.exceptions`, so `testcases.py` gains no pytest coupling
  (still verified by automated test). The module name and
  `get_excluded_admins` signature match what `coding-standards.md` already
  anticipated.
- **Testing**: the end-to-end test was explicitly verified non-vacuous by
  experiment (emptying `ADMIN_TESTS_EXCLUDE` makes it fail) — applying the
  lesson from run-003, where a negative-path test passed for the wrong
  reason.

### Design note recorded for `packaging-release-readiness`

Auto-collection is **opt-in** (`django_admin_tests_auto`, default false),
decided with the user during planning: installing a package must not
silently add tests that fail an existing CI. This makes the README's
quickstart a two-liner (install + one ini line) rather than truly
zero-config, and the README should say so plainly along with the three
`ADMIN_TESTS_*` settings.

---

## Standards Referenced

- `.specs-fire/standards/coding-standards.md`
- `.specs-fire/standards/testing-standards.md`
- `.specs-fire/standards/constitution.md`
- `.specs-fire/standards/system-architecture.md`
