---
id: packaging-release-readiness
title: PyPI packaging and release readiness
intent: core-package
complexity: low
mode: autopilot
status: completed
depends_on:
  - package-skeleton
  - pytest-plugin
created: 2026-08-06T20:27:17Z
run_id: run-django-admin-tests-007
completed_at: 2026-08-06T22:21:53.648Z
---

# Work Item: PyPI packaging and release readiness

## Description

Finalize pyproject.toml packaging metadata (name, version, description,
license, classifiers, README long_description, entry-point declaration for
the pytest11 plugin) and verify the package builds and installs cleanly, in
preparation for a first PyPI release.

## Acceptance Criteria

- [ ] pyproject.toml has complete project metadata (name, version, description, authors, license, classifiers, Python/Django version constraints)
- [ ] pytest11 entry point correctly declared and resolvable after install
- [ ] `python -m build` produces a valid sdist and wheel
- [ ] Installing the built wheel into a clean venv exposes AdminSmokeTestCase and (with pytest present) the auto-discovery plugin
- [ ] testapp/ and other dev-only files excluded from the built distribution
- [ ] README.md is suitable as PyPI long_description (renders without errors)

## Technical Notes

(none)

## Dependencies

- package-skeleton
- pytest-plugin
