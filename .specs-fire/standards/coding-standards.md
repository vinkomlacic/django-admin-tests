# Coding Standards

## Overview

Conventions for both the distributable library code (`django_admin_tests/`) and this repo's own internal test suite (`tests/`, `testapp/`).

## Code Formatting

**Tool**: ruff format
**Config**: `pyproject.toml`
**Enforcement**: CI-blocking

### Key Settings

- **Line length**: 88
- **Quote style**: double

## Linting

**Tool**: ruff
**Base Config**: default ruleset
**Strictness**: warnings block CI

### Key Rules

- `F401`: error — no unused imports
- `E501`: warn — prefer ruff format over manual wrapping
- **No `pytest` imports under `django_admin_tests/`**: enforced by convention (consider a custom ruff/import-linter rule) — the shipped library must stay runner-agnostic; pytest is only allowed under `django_admin_tests/pytest_plugin.py` and `tests/`.

## Naming Conventions

### Variables and Functions

| Element | Convention | Example |
|---------|------------|---------|
| Variables/functions | snake_case | `admin_url`, `get_registered_admins` |
| Classes | PascalCase | `AdminSmokeTestCase` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_ALLOWED_STATUS_CODES` |
| Test methods (this repo's own tests) | `test_<behavior>` | `test_one_method_is_generated_per_model_and_view` |
| Generated test methods (shipped) | `test_admin_smoke_<app_label>_<model_name>_<view>` | `test_admin_smoke_testapp_product_changelist` |

### Files and Folders

- **Shipped test classes**: `django_admin_tests/testcases.py`
- **Optional pytest plugin**: `django_admin_tests/pytest_plugin.py`
- **This repo's own test modules**: `tests/test_<subject>.py`
- **Internal sample app (dev-only)**: `testapp/` (models + admin registrations used only to test this library)

## File Organization

### Project Structure

```
django-admin-tests/
├── django_admin_tests/       # the shipped, installable package
│   ├── __init__.py
│   ├── testcases.py          # AdminSmokeTestCase (unittest-based, no pytest dependency)
│   ├── pytest_plugin.py      # optional pytest11 entry point for auto-discovery
│   └── apps.py                # AppConfig, for INSTALLED_APPS registration
├── testapp/                   # dev-only sample app, exercised by this repo's own tests
│   ├── models.py
│   ├── admin.py
│   └── migrations/
├── tests/                     # this repo's own test suite (pytest-django)
│   └── test_*.py
├── conftest.py
├── pyproject.toml             # packaging metadata + pytest11 entry point
└── README.md
```

### Conventions

- **Shipped code stays dependency-light**: `django_admin_tests/testcases.py` imports only Django, never pytest.
- **pytest is isolated to one module**: all pytest-specific glue lives in `pytest_plugin.py`, so it's obvious what's optional.
- **`testapp/` never ships**: excluded from the package build; exists only for this repo's own CI.

## Import Order

```python
# stdlib
import json

# third-party
from django.contrib import admin
from django.test import TestCase

# local
from django_admin_tests.settings import get_excluded_admins
```

**Rules**:
- Standard library, then third-party, then local imports, each group separated by a blank line.
- No wildcard imports.
- `django_admin_tests/testcases.py` must not import from `pytest_plugin.py` (keeps the core dependency-free).

## Error Handling

### Pattern

**Approach**: Fail loudly with clear assertion messages naming the offending `ModelAdmin`/URL; avoid silently skipping admins unless explicitly configured via an opt-out.

### Guidelines

- If a `ModelAdmin` can't be resolved to a URL (e.g., misconfigured `AdminSite`), raise/fail with the model name in the message rather than a bare `KeyError`.
- Configuration errors (e.g., invalid exclude list) should fail fast at test-setup time, not mid-loop.

### Example

```python
def _make_view_test(model, view_name):
    """Build one generated test method, closing over the model it covers."""

    def test(self):
        url = self._reverse_admin_url(model, view_name)
        response = self._get_admin_view(model, view_name, url)
        self._assert_allowed_status(model, view_name, response)

    test.__name__ = _generated_method_name(model, view_name)
    return test
```

The assertion message names the model (`_assert_allowed_status`), *and* so does
the test's own name — the second matters because that's what a CI report shows
before anyone opens the traceback.

## Logging

**Tool**: standard library `logging`
**Format**: N/A — not used in the shipped `TestCase`; test failures should be self-explanatory via assertion messages.

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Local troubleshooting only, not committed |

### Guidelines

**Always log**:
- Nothing by default in shipped code — prefer assertion messages over log output.

**Never log**:
- Credentials or session data used in test fixtures.

## Comments and Documentation

### When to Comment

- In `django_admin_tests/`, comment any Django-admin-internals workaround (e.g., handling `AdminSite` vs custom sites, URL name quirks) since these are non-obvious and easy to regress.
- In `tests/`/`testapp/`, comment only when a fixture encodes a non-obvious cross-runner behavior.

### Documentation Format

**Functions**: shipped public API (`AdminSmokeTestCase` and its methods) requires a docstring explaining behavior and any configuration hooks; internal test helpers don't need one.
**Classes**: every class under `django_admin_tests/` needs a one-line docstring; `testapp`/`tests` classes only when non-obvious.

## Code Patterns

### Preferred Patterns

#### Runner-agnostic core, pytest as an add-on

Keep all pytest-specific code isolated so the core (`testcases.py`) never imports it:

```python
# django_admin_tests/pytest_plugin.py
import pytest

from django_admin_tests.testcases import AdminSmokeTestCase


def pytest_collectstart(collector):
    ...  # registers AdminSmokeTestCase for pytest collection
```

#### One generated test method per admin

Generate a separate test method per (registered model, view) at class-creation time rather than looping the registry inside a single test. One failing admin then fails under its own name, can be re-run on its own, and doesn't hide failures in others — which matters more here than in typical apps because a host project can register dozens of admins.

`subTest` was the previous approach and is no longer used: it collapses every model into one test identity, so the report can't say *which* admin broke without reading the message, and there's no way to select a single model.

### Anti-Patterns to Avoid

- **pytest fixtures/parametrize in shipped code**: breaks the `manage.py test` path entirely — not just a style issue, a hard compatibility bug.
- **Testing Django internals**: don't re-test framework behavior (e.g., that `ModelAdmin.save_model` calls `.save()`) — only test what this library adds.
- **Assuming a single `AdminSite`**: host projects may register custom `AdminSite` instances; don't hardcode `django.contrib.admin.site`.

---
*Generated by specs.md - fabriqa.ai FIRE Flow*
