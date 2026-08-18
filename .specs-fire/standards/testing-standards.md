# Testing Standards

## Overview

This repo has two distinct testing contexts, and they follow different rules:

1. **Test code we ship** (the public API, e.g. `AdminSmokeTestCase`) — runs *inside consumers' projects*, under either Django's native runner or pytest. It must be written in a runner-agnostic style.
2. **Tests of this library itself** (in `tests/`, using the internal `testapp`) — only ever run in this repo's own CI, so they're free to use pytest-native conveniences.

Never mix the two: code under `django_admin_tests/` (shipped) must not depend on pytest; code under `tests/` (this repo's own suite) may.

## Testing Framework

**Framework (shipped code)**: `unittest` / Django `TestCase` — must run under both `manage.py test` and pytest.
**Framework (this repo's own tests)**: pytest + pytest-django
**Runner (this repo's own tests)**: pytest-django

## Test Types

| Type | Tool | Location | When to Use |
|------|------|----------|-------------|
| Public API (shipped) | Django `TestCase` (unittest) | `django_admin_tests/testcases.py` | Any test logic that will run inside a consumer's project |
| Library self-tests | pytest + pytest-django | `tests/test_*.py` | Verifying `AdminSmokeTestCase`/plugin behavior against the internal `testapp`, under both `manage.py test` and pytest |
| Cross-runner verification | pytest-django AND `manage.py test`, both in CI | `tests/` (same files, both invocations) | Confirming shipped `TestCase`s actually work under both runners, not just pytest |

## Coverage Requirements

**Target**: 90%
**Enforcement**: CI-blocking on `django_admin_tests/` (the shipped, public-facing code); informational on `tests/`/`testapp/`

**Critical paths that MUST have coverage:**
- `AdminSmokeTestCase` view resolution and assertion logic
- Admin registry iteration, including edge cases (no registered admins, inline-only admins, custom `AdminSite` instances)
- pytest plugin discovery/registration path
- Opt-out/configuration mechanism for excluding specific `ModelAdmin`s

## Test Naming

**Pattern**: `test_<subject>_<behavior>`

**Examples**:
- `test_one_method_is_generated_per_model_and_view` — verifies the core smoke-test behavior
- `test_pytest_plugin_discovers_without_import` — verifies zero-config discovery under pytest
- `test_manage_py_test_runs_shipped_testcase` — verifies the native-runner path works with only a one-line import

The *generated* methods shipped to consumers follow a separate pattern —
`test_admin_smoke_<app_label>_<model_name>_<view>`, e.g.
`test_admin_smoke_testapp_product_changelist` — since their names are built
at runtime from the admin registry rather than written by hand.

## Test Structure

Shipped code (`django_admin_tests/testcases.py`) — plain Django `TestCase`, no pytest fixtures:

```python
from django.contrib import admin
from django.test import TestCase


class AdminSmokeMeta(type):
    """Binds one test method per (registered model, view) onto the class."""

    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        for method_name, method in _build_generated_tests(cls.admin_site).items():
            setattr(cls, method_name, method)
        return cls


class AdminSmokeTestCase(TestCase, metaclass=AdminSmokeMeta):
    admin_site = admin.site
```

A metaclass rather than `__init_subclass__`: the latter doesn't fire for the
class that defines it, which would leave the base class — the one the pytest
plugin collects directly — carrying no tests at all.

This repo's own tests (`tests/test_admin_smoke.py`) — pytest-native, exercising the above against `testapp`:

```python
def test_smoke_testcase_passes_against_testapp(django_testdir):
    ...
```

## Mock Strategy

**Approach**: Prefer real Django admin objects, the real registry, and the test client over mocking; mock only true external boundaries (there currently are none).

**Guidelines**:
- Don't mock `django.contrib.admin.site._registry` in the shipped `TestCase` — it must read the host project's real registry.
- In this repo's own tests, use the real `testapp` registry rather than faking admin registrations.

## Test Data

**Strategy**: pytest fixtures in `conftest.py` for this repo's own tests; the shipped `TestCase` creates only the minimal objects it needs (e.g., one instance per model) to exercise change views, or skips change-view assertions when no instance exists and none can be trivially created.

**Guidelines**:
- Keep `testapp` fixtures minimal — just enough to have at least one object per registered model.
- The shipped `TestCase` must not assume the host project's fixtures/factories; it should be self-sufficient or clearly document what it needs.

## Running Tests

```bash
# This repo's own suite (pytest)
pytest

# This repo's own suite, via Django's native runner (cross-runner check).
# Scope it to `tests` — an unscoped run makes Django's `test*.py` discovery
# pattern match django_admin_tests/testcases.py and run the un-subclassed
# base class, which correctly fails on testapp's permission-denying admin.
# This is the invocation CI uses.
python manage.py test tests

# With coverage
pytest --cov=django_admin_tests --cov-report=term-missing

# Single file
pytest tests/test_admin_smoke.py
```

## CI/CD Integration

**Pipeline**: GitHub Actions
**Trigger**: on push and pull_request

**Required gates**:
- `pytest` passes (this repo's own suite)
- `manage.py test` passes (cross-runner check on the shipped `TestCase`)
- `ruff check` passes
- `ruff format --check` passes
- Matrix: supported Python × Django version combinations

---
*Generated by specs.md - fabriqa.ai FIRE Flow*
