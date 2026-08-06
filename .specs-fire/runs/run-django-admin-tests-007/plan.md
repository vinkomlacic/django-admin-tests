---
run: run-django-admin-tests-007
work_item: packaging-release-readiness
intent: core-package
mode: autopilot
checkpoint: none
approved_at: n/a
---

# Implementation Plan: PyPI packaging and release readiness

## Approach

Finish the metadata and documentation needed to publish, and verify the
built artifacts by installing them into a clean environment rather than by
inspecting the wheel listing alone.

Two pieces of accumulated debt land here, both flagged in earlier runs'
review reports:

1. **The README is a single title line.** It's the PyPI long_description,
   so it's also the entire product pitch. It must document the real
   install story — including that auto-collection is opt-in
   (`django_admin_tests_auto = true`), not literally zero-config — plus
   the three `ADMIN_TESTS_*` settings, the subclassing path, and how to
   exclude the tests under each runner.
2. **Missing metadata**: project URLs, keywords, and a CI badge now that a
   workflow exists.

`version` stays `0.1.0.dev0` — deciding the actual release number is the
user's call, not something to slip into a packaging task.

## Files to Create

| File | Purpose |
|------|---------|
| `LICENSE` | `pyproject.toml` declares MIT but no license file exists; PyPI and downstream packagers expect one |
| `CHANGELOG.md` | Constitution requires migration notes for breaking changes; start the record at 0.1.0 |

## Files to Modify

| File | Changes |
|------|---------|
| `README.md` | Full rewrite: what it does, install, both usage paths (plugin + subclass), settings reference, exclusion, limitations |
| `pyproject.toml` | Add `[project.urls]`, `keywords`; confirm `license`/`readme` wiring |

## Tests

| Test File | Coverage |
|-----------|----------|
| (existing suite) | Must remain green; no behavior changes in this item |

Verification is packaging-level rather than unit-level:

- `python -m build` produces both sdist and wheel
- **Install the built wheel into a fresh venv** and import
  `AdminSmokeTestCase` + confirm the `pytest11` entry point resolves —
  wheel contents alone don't prove installability
- Inspect the **sdist** too (previous runs only checked the wheel), since
  that's what source-based installs consume
- `twine check` on both artifacts to catch long_description rendering
  errors before upload

## Technical Details

The README's limitations section should be honest about what earlier runs
uncovered: models whose change view can't be auto-instantiated are skipped
with a warning, custom `AUTH_USER_MODEL` support is `user_factory`-only,
and importing `AdminSmokeTestCase` by name into a test module causes test
discovery to collect the base class too.

---
*Plan generated for autopilot mode — no checkpoint pause. Proceeding directly to implementation.*
