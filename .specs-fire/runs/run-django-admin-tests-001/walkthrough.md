---
run: run-django-admin-tests-001
work_item: package-skeleton
intent: core-package
generated: 2026-08-06T20:47:00Z
mode: autopilot
---

# Implementation Walkthrough: Package skeleton and build config

## Summary

Scaffolded the installable `django-admin-tests` package: a `pyproject.toml`
(hatchling backend, Django-only prod dependency, ruff config, `pytest11`
entry point) and the `django_admin_tests/` package with an `AppConfig` and
stub `testcases.py`/`pytest_plugin.py` modules that later work items will
fill in. Added a matching `tests/` directory for this repo's own suite and
verified the package installs, imports, lints, formats, and builds cleanly.

## Structure Overview

Two independent trees now exist side by side: `django_admin_tests/`, the
package that will ship to PyPI, and `tests/`, this repo's own pytest suite
that exercises it (never shipped, excluded from the wheel). The shipped
package is intentionally inert at this stage — `testcases.py` and
`pytest_plugin.py` are docstring-only stubs — so this work item validates
the *packaging and tooling* rather than any admin-testing behavior, which
starts with the next work item (`dev-testapp`).

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build backend (hatchling), project metadata, `django>=4.2` dependency, dev/pytest optional-dependency groups, ruff config, `pytest11` entry point |
| `django_admin_tests/__init__.py` | Package marker, `__version__` |
| `django_admin_tests/apps.py` | `DjangoAdminTestsConfig` `AppConfig` for `INSTALLED_APPS` |
| `django_admin_tests/testcases.py` | Stub for `AdminSmokeTestCase` — docstring only, no pytest import |
| `django_admin_tests/pytest_plugin.py` | Stub for the optional `pytest11` plugin — docstring only |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Placeholder for this repo's own pytest fixtures |
| `tests/test_package_skeleton.py` | Verifies import, `__version__`, `AppConfig.name`, and that `testcases.py` imports no `pytest` (via `ast`, not string search) |
| `.gitignore` | Standard Python/build ignores, plus `node_modules/` for the FIRE tooling scripts under `.specsmd/` |

### Modified

| File | Changes |
|------|---------|
| (none) | |

## Key Implementation Details

### 1. Wheel scoping via `[tool.hatch.build.targets.wheel] packages`

Explicitly listed `django_admin_tests` as the only packaged directory so
`tests/` (and any future dev-only `testapp/`) never ends up in the
distributed wheel, without relying on `.gitignore`-style exclude patterns.

### 2. `pytest11` entry point registered from day one

The entry point is declared and points at the still-empty
`pytest_plugin.py` stub. This was verified to actually resolve: `pytest`
picked it up automatically in this repo's own test run (`plugins: ...,
django-admin-tests-0.1.0.dev0` in the pytest header) and the built wheel's
`entry_points.txt` contains the correct `[pytest11]` mapping — so later
work items can add real plugin logic without touching packaging.

### 3. ruff scoped away from FIRE's own directories

`ruff format --check .` initially flagged two files under
`.specs-fire/standards/*.md` because ruff format also reformats Python code
fences inside Markdown. Added `extend-exclude = [".specs-fire", ".specsmd",
"node_modules"]` so ruff only ever touches this repo's actual code, not
FIRE's generated docs/tooling.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| License | MIT (placeholder) | Common default for Django ecosystem packages; final call belongs to the `packaging-release-readiness` work item, which owns full metadata polish |
| pytest as optional extra | `pip install django-admin-tests[pytest]` | Matches tech-stack.md: pytest is never required for the `manage.py test` path |
| Dev tooling install | `pip install -e ".[dev]"` (pytest, pytest-django, ruff) | Matches tech-stack.md's declared dev dependencies |

## Deviations from Plan

None — implementation matched `plan.md` exactly.

## Dependencies Added

| Package | Why Needed |
|---------|------------|
| `django>=4.2` | Prod dependency; the framework this library tests |
| `pytest`, `pytest-django`, `ruff` (dev extra) | This repo's own test/lint tooling, per tech-stack.md |
| `yaml` (npm, root `package.json`) | Required by FIRE's own `init-run.cjs`/`complete-run.cjs` scripts under `.specsmd/`, not part of the shipped Python package |

## How to Verify

1. **Install editable with dev extras**

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```

   Expected: installs cleanly, no errors.

2. **Run the test suite**

   ```bash
   pytest tests/
   ```

   Expected: `3 passed`, and the plugin line in the pytest header includes
   `django-admin-tests-0.1.0.dev0`.

3. **Lint and format check**

   ```bash
   ruff check . && ruff format --check .
   ```

   Expected: both report no issues.

4. **Build and inspect the wheel**

   ```bash
   python -m build --wheel -o /tmp/dab-build
   unzip -l /tmp/dab-build/*.whl
   ```

   Expected: only `django_admin_tests/` package files plus dist-info —
   no `tests/`, no FIRE artifacts.

## Test Coverage

- Tests added: 3
- Coverage: 100%
- Status: passing

## Ready for Review

- [x] All acceptance criteria met
- [x] Tests passing
- [x] No critical issues
- [ ] Documentation updated (if applicable)
- [x] Developer notes captured

## Developer Notes

- A Python virtualenv was created at `.venv/` for verification during this
  run (gitignored). Use it (or your own) for subsequent work items.
- Running FIRE's own scripts required `npm install yaml` at the repo root,
  producing `package.json`/`package-lock.json`/`node_modules/`. These are
  FIRE tooling artifacts, not part of the shipped Python package;
  `node_modules/` is gitignored, but `package.json`/`package-lock.json`
  remain tracked as the manifest for that tooling dependency.
- `testcases.py` and `pytest_plugin.py` are currently docstring-only stubs
  by design — real behavior lands in `admin-smoke-testcase-core` and
  `pytest-plugin` respectively. Don't be alarmed that `grep`-ing for
  `AdminSmokeTestCase` finds nothing yet.

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-001*
