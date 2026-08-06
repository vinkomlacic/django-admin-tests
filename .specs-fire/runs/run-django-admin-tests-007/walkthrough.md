---
run: run-django-admin-tests-007
work_item: packaging-release-readiness
intent: core-package
generated: 2026-08-07T01:20:00Z
mode: autopilot
---

# Implementation Walkthrough: PyPI packaging and release readiness

## Summary

Completed the metadata, license, changelog and README needed to publish,
and verified the artifacts by installing them into clean virtualenvs rather
than by reading wheel listings. Two problems surfaced that had been hiding
behind weaker checks in earlier runs: the sdist was shipping the entire
repository, and the "100% coverage" reported six times had never been
measured.

## Structure Overview

The package itself didn't change. What changed is everything around it:
`README.md` went from a one-line stub to the actual PyPI long_description,
`LICENSE` and `CHANGELOG.md` now exist, `pyproject.toml` gained URLs,
keywords, an sdist allowlist and coverage configuration, and CI gained a
coverage job so the gate in `testing-standards.md` is enforced instead of
assumed.

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `LICENSE` | MIT text; `pyproject.toml` declared MIT but no file existed |
| `CHANGELOG.md` | Release record, starting at the unreleased 0.1.0 feature set |

### Modified

| File | Changes |
|------|---------|
| `README.md` | Full rewrite: usage (both paths), settings reference, factories, exclusion, known limitations |
| `pyproject.toml` | `[project.urls]`, `keywords`, `license-files`, sdist allowlist, coverage config, expanded dev extras |
| `.github/workflows/ci.yml` | Coverage job enforcing `fail_under = 90` |
| `tests/test_admin_smoke.py`, `tests/test_instantiation.py`, `tests/test_pytest_plugin.py` | Tests closing every real coverage gap |

## Key Implementation Details

### 1. The sdist was shipping the whole repository

`hatchling`'s `packages` setting scopes the **wheel only**. The sdist swept
in `.claude/settings.local.json` (containing absolute developer paths), the
entire `.specsmd/` tooling, and every internal `.specs-fire/` planning
document — 136K bound for PyPI. Fixed with an explicit sdist allowlist;
now 24K containing the package, tests, testapp and standard metadata.

Earlier runs verified only the wheel, which is why this went unnoticed for
six runs. Publishing is irreversible, so it mattered that the plan called
for inspecting the sdist specifically.

### 2. The coverage figure was invented, and the tool was lying too

Runs 001–006 each reported "100% coverage". None had run a coverage tool.
Installing `coverage` revealed **92%**, with genuinely untested paths
including `user_factory` — a public API this very run was documenting in
the README.

Then a second layer: `pytest --cov` reports **86%**, understating by ~13
points, because `django_admin_tests` is imported through its own `pytest11`
entry point while pytest loads plugins — before pytest-cov starts tracing —
so module-level lines and `def` statements read as never executed.
`coverage run -m pytest` starts tracing first and reports the truth.

Both are now addressed: tests fill every real gap (99%), the correct
invocation is pinned in `[tool.coverage.run]` with an explanatory comment,
and CI enforces the threshold.

### 3. The first clean-install check proved nothing

`python -c "import django_admin_tests"` run from the project directory
imports the **source tree**, because Python puts the cwd on `sys.path`. The
check passed and was meaningless. Re-run from outside the source tree with
an assertion that the module resolves under `site-packages` — which is what
makes a clean-install test a test.

### 4. Documenting the rough edges

The README states plainly that the pytest plugin is opt-in (not zero-config),
that un-instantiable models are skipped rather than failed, that custom
`AUTH_USER_MODEL` support is the `user_factory` hook only, and that
importing `AdminSmokeTestCase` by name causes discovery to collect the base
class too. Users meet all four on day one.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Version number | Left at `0.1.0.dev0` | Choosing a release number is the user's call, not a packaging side effect |
| sdist contents | Explicit allowlist, keeping `tests/` and `testapp/` | Allowlists fail closed; downstream packagers expect to run the suite from source |
| Coverage invocation | `coverage run -m pytest`, pinned in config | `pytest --cov` structurally cannot measure this package correctly |
| Coverage gate | Added to CI | `testing-standards.md` calls it CI-blocking; it had never been enforced |

## Deviations from Plan

The plan didn't anticipate fixing coverage gaps — that work appeared once
the number was actually measured. Everything else matched.

## Dependencies Added

`coverage`, `build` and `twine` added to the **dev** extra only. No change
to what consumers install: still Django alone.

## How to Verify

1. **Build and check the artifacts**

   ```bash
   source .venv/bin/activate
   python -m build && python -m twine check dist/*
   ```

   Expected: both PASSED.

2. **Confirm the sdist is clean**

   ```bash
   tar tzf dist/*.tar.gz | grep -E "\.claude|\.specsmd|\.specs-fire" || echo "clean"
   ```

   Expected: `clean`.

3. **Coverage, measured correctly**

   ```bash
   coverage run -m pytest tests/ && coverage report
   ```

   Expected: 99%, and a non-zero exit if it ever drops below 90.

4. **Clean install — from outside the source tree**

   ```bash
   python -m venv /tmp/v && /tmp/v/bin/pip install dist/*.whl
   cd /tmp && /tmp/v/bin/python -c "import django_admin_tests as d; print(d.__file__)"
   ```

   Expected: a path under `site-packages`, not this repo.

## Test Coverage

- Tests added: 79 total in suite (14 new this work item) + 20 subtests
- Coverage: 99% (measured, not assumed); 2 uncovered lines run only in the pytester subprocess
- Status: passing

## Ready for Review

- [x] All acceptance criteria met
- [x] Tests passing
- [x] No critical issues
- [x] Documentation updated
- [x] Developer notes captured

## Developer Notes

- **Use `coverage run -m pytest`, never `pytest --cov`** for this package.
  The latter reports ~13 points low for structural reasons, not because
  anything is untested. The reason is commented in `pyproject.toml` so the
  next person doesn't "fix" it back.
- **Check the sdist, not just the wheel**, after any packaging change.
  They're built by different hatchling configuration and can diverge
  silently.
- `version = "0.1.0.dev0"` and the changelog's `[Unreleased]` heading both
  need updating when you decide to tag a release.
- Coverage exempts nothing via `# pragma: no cover`. The 2 uncovered lines
  are genuinely exercised — by the pytester subprocess test — just not
  visible to the parent tracer. Worth remembering before anyone "cleans
  them up".

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-007*
