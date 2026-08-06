---
run: run-django-admin-tests-001
work_item: package-skeleton
intent: core-package
mode: autopilot
checkpoint: none
approved_at: n/a
---

# Implementation Plan: Package skeleton and build config

## Approach

Scaffold the installable `django-admin-tests` package per
`coding-standards.md`'s file organization: `pyproject.toml` (hatchling
backend, Django>=4.2 as the only prod dependency, ruff config, optional
`pytest`/`pytest-django` dev dependencies), the `django_admin_tests/`
package with stub `testcases.py`, `pytest_plugin.py`, and `apps.py`, plus a
`tests/` directory with `conftest.py` for this repo's own pytest-based
suite. Stub modules contain only docstrings/minimal placeholders — no
behavior yet (later work items implement `AdminSmokeTestCase` and the
plugin). Verify the package installs editable and imports cleanly.

## Files to Create

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build backend (hatchling), project metadata, Django>=4.2 dependency, dev/optional deps (pytest, pytest-django, ruff), ruff config |
| `django_admin_tests/__init__.py` | Package marker, `__version__` |
| `django_admin_tests/apps.py` | `AppConfig` for `INSTALLED_APPS` registration |
| `django_admin_tests/testcases.py` | Stub for `AdminSmokeTestCase` (docstring only, no pytest import) |
| `django_admin_tests/pytest_plugin.py` | Stub for the optional `pytest11` plugin (docstring only) |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Placeholder pytest fixtures/config for this repo's own suite |
| `.gitignore` | Standard Python/build ignores (`__pycache__`, `*.egg-info`, `build/`, `dist/`, `.venv`, node_modules from FIRE tooling) |

## Files to Modify

| File | Changes |
|------|---------|
| (none) | |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_package_skeleton.py` | Package imports cleanly, `__version__` is set, `testcases.py` never imports pytest, `apps.py` exposes a valid `AppConfig` |

## Technical Details

- Build backend: `hatchling`, per `tech-stack.md`.
- Prod dependency: `django>=4.2` only.
- Dev/optional dependency groups: `[project.optional-dependencies].dev` = `pytest`, `pytest-django`, `ruff` (per tech-stack.md); a `pytest` extra reserved for consumers wanting the plugin, declared as `[project.optional-dependencies].pytest = ["pytest"]`.
- `pytest11` entry point declared as a placeholder now (`[project.entry-points.pytest11]`) pointing at the stub `pytest_plugin` module — full auto-discovery logic lands in the `pytest-plugin` work item.
- ruff config: line-length 88, double quotes, default ruleset, `F401` as error — per `coding-standards.md`.
- No functional test coverage target applies yet (0% for `django_admin_tests/` is expected at this stage — enforcement of the 90% target starts once `AdminSmokeTestCase` ships).

---
*Plan generated for autopilot mode — no checkpoint pause. Proceeding directly to implementation.*
