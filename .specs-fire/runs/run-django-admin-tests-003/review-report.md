# Code Review Report

**Run**: run-django-admin-tests-003
**Intent**: core-package
**Reviewed**: 2026-08-06T21:30:00Z
**Files Reviewed**: 4

---

## Summary

| Category | Auto-Fixed | Applied | Skipped |
|----------|------------|---------|---------|
| Code Quality | 1 | 0 | 0 |
| Security | 0 | 0 | 0 |
| Architecture | 0 | 0 | 0 |
| Testing | 0 | 2 | 0 |
| **Total** | **1** | **2** | **0** |

**Tests Status**: Passing (13 tests, 12 subtests)

---

## Files Reviewed

- `django_admin_tests/testcases.py` (source, modified — full implementation)
- `tests/test_admin_smoke.py` (test, created)
- `tests/custom_admin_site_urls.py` (test fixture, created during review)
- `pyproject.toml` (config, modified)

---

## Auto-Fixed Issues

### 1. [Code Quality] Line-length formatting in `_reverse_admin_url`

- **File**: `django_admin_tests/testcases.py:71`
- **Description**: `ruff format` wrapped a long f-string assignment and
  unwrapped a short `self.fail(...)` call. Purely mechanical.
- **Diff**: whitespace/wrapping only; `pytest tests/` re-run after the fix —
  still fully passing.

---

## Applied Suggestions

### 1. [Testing] Negative-path test was passing vacuously — CRITICAL

- **File**: `tests/test_admin_smoke.py:35`
- **Description**: The test drove the case via `case.run(result)`. Django's
  `SimpleTestCase._pre_setup` (which creates `self.client`) runs from
  `__call__`, not from `run` — so the case errored on a missing `client`
  attribute, and `assert not result.wasSuccessful()` passed regardless of
  whether the deliberately-broken admin was ever detected. The single most
  important test in this work item was verifying nothing.
- **Rationale**: A negative-path test that can't distinguish "detected the
  bug" from "crashed before looking" provides false confidence in exactly
  the guarantee this library exists to make.
- **Risk Level**: High (test-only code, but it invalidated the work item's
  headline acceptance criterion)
- **Approved**: 2026-08-06T21:28:00Z
- **Diff**: `case.run(result)` → `case(result)`, plus a new assertion that
  the failure text actually contains the injected `"boom"` error, so the
  test cannot regress to vacuous. Inline comment added explaining the
  `run` vs `__call__` distinction.

### 2. [Testing] Missing critical-path coverage required by standards

- **File**: `tests/test_admin_smoke.py`
- **Description**: `testing-standards.md` names "no registered admins" and
  "custom `AdminSite` instances" as MUST-have coverage for
  `AdminSmokeTestCase`; neither existed.
- **Rationale**: Coverage on `django_admin_tests/` is CI-blocking per the
  standards, and the custom-`AdminSite` case is precisely what the
  `admin_site.name`-based URL resolution was designed for — untested, the
  design's central claim was unverified.
- **Risk Level**: Medium
- **Approved**: 2026-08-06T21:28:00Z (user-confirmed)
- **Diff**: Added `test_admin_smoke_handles_empty_registry` and
  `test_admin_smoke_supports_custom_admin_site`, plus
  `tests/custom_admin_site_urls.py` providing a real URLconf for a
  non-default-named `AdminSite`.

---

## Skipped Suggestions

No suggestions were skipped.

---

## Project Tooling Used

- **ruff (lint)**: `pyproject.toml` — `ruff check .` passes
- **ruff (format)**: `pyproject.toml` — `ruff format --check .` passes

Manual review against `review-categories.md`:
- **Security**: the disposable superuser's password is a test-only literal
  created inside a rolled-back test transaction — same accepted pattern as
  `tests/settings.py`'s `SECRET_KEY`, not a real secret. No injection
  surface (all URLs come from `reverse()`, never string concatenation of
  user input).
- **Architecture**: `testcases.py` imports only from `django.*` — verified
  by an existing automated test, not just inspection. No import of
  `pytest_plugin`, per `coding-standards.md`.
- **Code Quality**: `subTest` used per-admin as the standards require;
  assertion messages name the offending model and view, per the error
  handling guidance.

### Note for a later work item

The design doc listed "pytest users have no built-in equivalent to
`--exclude-tag`" as a risk to be handled in `pytest-plugin`. This turns
out to be a non-issue: **pytest-django already maps `django.test.tag()`
onto pytest markers**, verified in this run — `pytest -m
django_admin_tests` and `pytest -m "not django_admin_tests"` both filter
correctly with no plugin code. The marker was registered in
`pyproject.toml` to silence `PytestUnknownMarkWarning`. The
`pytest-plugin` work item can drop that risk.

---

## Standards Referenced

- `.specs-fire/standards/coding-standards.md`
- `.specs-fire/standards/testing-standards.md`
- `.specs-fire/standards/constitution.md`
- `.specs-fire/intents/core-package/work-items/admin-smoke-testcase-core-design.md`
