---
id: pytest-plugin
title: Optional pytest11 auto-discovery plugin
intent: core-package
complexity: medium
mode: confirm
status: completed
depends_on:
  - admin-smoke-testcase-core
created: 2026-08-06T20:27:17Z
run_id: run-django-admin-tests-005
completed_at: 2026-08-06T21:59:37.573Z
---

# Work Item: Optional pytest11 auto-discovery plugin

## Description

Implement `django_admin_tests/pytest_plugin.py` as an optional `pytest11`
entry-point plugin that auto-discovers and registers AdminSmokeTestCase-based
tests under pytest with zero host-side code (no manual import needed). Must
not be required for, or interfere with, the `manage.py test` path.

## Acceptance Criteria

- [ ] `pytest_plugin.py` registered via `pytest11` entry point in pyproject.toml
- [ ] When pytest + pytest-django are installed in a host project, admin smoke tests are collected and run without any import in the host project's own test files
- [ ] Plugin code only loads/executes when pytest is present (never imported by testcases.py or any manage.py test path)
- [ ] Running pytest against testapp collects and passes the smoke tests
- [ ] Running `manage.py test` against testapp continues to pass unaffected by the plugin's presence

## Technical Notes

(none)

## Dependencies

- admin-smoke-testcase-core
