---
id: run-django-admin-tests-005
scope: single
work_items:
  - id: pytest-plugin
    intent: core-package
    mode: confirm
    status: completed
    current_phase: review
    checkpoint_state: approved
    current_checkpoint: plan
current_item: null
status: completed
started: 2026-08-06T21:40:57.953Z
completed: 2026-08-06T21:59:37.573Z
---

# Run: run-django-admin-tests-005

## Scope
single (1 work item)

## Work Items
1. **pytest-plugin** (confirm) — completed


## Current Item
(all completed)

## Files Created
- `django_admin_tests/settings.py`: Django-settings-based configuration accessors
- `tests/test_settings.py`: Settings accessor tests
- `tests/test_pytest_plugin.py`: Plugin tests incl. end-to-end pytester subprocess run

## Files Modified
- `django_admin_tests/pytest_plugin.py`: Implemented opt-in auto-collection, marker registration, graceful degradation
- `django_admin_tests/testcases.py`: Class attrs default to None; settings-aware resolution; exclusion support
- `pyproject.toml`: Removed redundant marker registration; documented why auto-collection stays off here
- `tests/conftest.py`: Enabled the pytester plugin
- `tests/test_admin_smoke.py`: Resolution-order and exclusion tests

## Decisions
(none)


## Summary

- Work items completed: 1
- Files created: 3
- Files modified: 5
- Tests added: 65
- Coverage: 100%
- Completed: 2026-08-06T21:59:37.573Z
