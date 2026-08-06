---
id: run-django-admin-tests-004
scope: single
work_items:
  - id: change-view-instantiation
    intent: core-package
    mode: validate
    status: completed
    current_phase: review
    checkpoint_state: approved
    current_checkpoint: plan
current_item: null
status: completed
started: 2026-08-06T21:27:38.761Z
completed: 2026-08-06T21:35:26.030Z
---

# Run: run-django-admin-tests-004

## Scope
single (1 work item)

## Work Items
1. **change-view-instantiation** (validate) — completed


## Current Item
(all completed)

## Files Created
- `django_admin_tests/factories.py`: Per-model factory registry (no Django imports)
- `django_admin_tests/instantiation.py`: In-house minimal-instance builder + AdminSmokeWarning
- `testapp/migrations/0002_selfreferentialitem.py`: Migration for the unbuildable-model fixture
- `tests/test_factories.py`: Registry tests
- `tests/test_instantiation.py`: Builder unit tests: field mapping, FK reuse, cycle detection

## Files Modified
- `django_admin_tests/__init__.py`: Re-export register_factory/unregister_factory/clear_factories
- `django_admin_tests/testcases.py`: Added change-view test, _get_change_view_instance, args on _reverse_admin_url
- `testapp/models.py`: Added SelfReferentialItem (required self-FK)
- `testapp/admin.py`: Registered SelfReferentialItemAdmin
- `tests/conftest.py`: Autouse fixture clearing the global factory registry between tests
- `tests/test_admin_smoke.py`: Change-view success, skip+warning, factory precedence and resolution-order tests

## Decisions
(none)


## Summary

- Work items completed: 1
- Files created: 5
- Files modified: 6
- Tests added: 45
- Coverage: 100%
- Completed: 2026-08-06T21:35:26.030Z
