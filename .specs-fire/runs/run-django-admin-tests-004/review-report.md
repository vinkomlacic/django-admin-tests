# Code Review Report

**Run**: run-django-admin-tests-004
**Intent**: core-package
**Reviewed**: 2026-08-06T21:50:00Z
**Files Reviewed**: 11

---

## Summary

| Category | Auto-Fixed | Applied | Skipped |
|----------|------------|---------|---------|
| Code Quality | 1 | 0 | 0 |
| Security | 0 | 0 | 0 |
| Architecture | 0 | 1 | 0 |
| Testing | 0 | 0 | 0 |
| **Total** | **1** | **1** | **0** |

**Tests Status**: Passing (45 passed, 1 skipped by design, 20 subtests)

---

## Files Reviewed

- `django_admin_tests/factories.py` (source, created)
- `django_admin_tests/instantiation.py` (source, created)
- `django_admin_tests/__init__.py` (source, modified)
- `django_admin_tests/testcases.py` (source, modified)
- `testapp/models.py` (source, modified)
- `testapp/admin.py` (source, modified)
- `testapp/migrations/0002_selfreferentialitem.py` (generated)
- `tests/conftest.py` (test, modified)
- `tests/test_factories.py` (test, created)
- `tests/test_instantiation.py` (test, created)
- `tests/test_admin_smoke.py` (test, modified)

---

## Auto-Fixed Issues

### 1. [Code Quality] Formatting of the new model and test files

- **File**: `testapp/models.py`, `tests/test_admin_smoke.py`
- **Description**: `ruff format` wrapped a long `ForeignKey(...)` call and
  adjusted assertion wrapping. Mechanical only.
- **Diff**: whitespace/wrapping; suite re-run after — still 45 passing.

---

## Applied Suggestions

### 1. [Architecture] Hardcoded UTC datetime ignored the `USE_TZ` setting

- **File**: `django_admin_tests/instantiation.py:96`
- **Description**: `DateTimeField` values were built with
  `datetime.datetime.now(tz=datetime.timezone.utc)` and `DateField` with
  `datetime.date.today()`. An always-aware datetime is wrong for projects
  running `USE_TZ = False`, where Django warns about aware values (and the
  reverse warning fires for naive values when `USE_TZ = True`).
- **Rationale**: `django.utils.timezone.now()` exists precisely to return
  the correct kind for the active setting. Since this library runs inside
  arbitrary host projects, it can't assume either configuration — and this
  repo's own `tests/settings.py` sets `USE_TZ = True`, so the bug would
  never have surfaced locally.
- **Risk Level**: Medium (silent warnings / potential comparison bugs in
  consumer projects with `USE_TZ = False`)
- **Approved**: 2026-08-06T21:48:00Z
- **Diff**: `datetime.datetime.now(tz=...)` → `timezone.now()`;
  `datetime.date.today()` → `timezone.now().date()`;
  `datetime.datetime.now().time()` → `timezone.now().time()`.

---

## Skipped Suggestions

No suggestions were skipped.

---

## Project Tooling Used

- **ruff (lint)**: `pyproject.toml` — `ruff check .` passes
- **ruff (format)**: `pyproject.toml` — `ruff format --check .` passes

Manual review against `review-categories.md`:

- **Security**: no new dependency surface (the explicit constraint of this
  intent is upheld — `instantiation.py` imports only stdlib plus
  `django.db.models`/`django.utils.timezone`). All created rows live inside
  the per-test transaction and roll back.
- **Architecture**: module split holds up — `factories.py` has zero Django
  imports, so re-exporting from `__init__.py` can't trip app-registry
  loading. `testcases.py` still imports no pytest (verified by test).
- **Code Quality**: `isinstance` ordering in `value_for_field` is
  load-bearing (`EmailField`/`URLField`/`SlugField` subclass `CharField`)
  and is commented as such, so a future reorder won't silently break it.

### Deliberate behavior worth noting (not a defect)

A *registered* factory that raises is **not** caught — the exception
propagates and fails the test, rather than falling through to the
skip+warning path. This is intentional: a user who explicitly registered a
factory wants to know it's broken, whereas the auto-builder failing is an
expected, routine outcome. Documented here so it isn't "fixed" later by
mistake.

---

## Standards Referenced

- `.specs-fire/standards/coding-standards.md`
- `.specs-fire/standards/testing-standards.md`
- `.specs-fire/standards/constitution.md`
- `.specs-fire/intents/core-package/work-items/change-view-instantiation-design.md`
