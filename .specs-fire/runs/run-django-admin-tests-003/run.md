---
id: run-django-admin-tests-003
scope: single
work_items:
  - id: admin-smoke-testcase-core
    intent: core-package
    mode: validate
    status: completed
    current_phase: review
    checkpoint_state: approved
    current_checkpoint: plan
current_item: null
status: completed
started: 2026-08-06T21:06:33.080Z
completed: 2026-08-06T21:19:59.176Z
---

# Run: run-django-admin-tests-003

## Scope
single (1 work item)

## Work Items
1. **admin-smoke-testcase-core** (validate) — completed


## Current Item
(all completed)

## Files Created
- `tests/test_admin_smoke.py`: Dogfood subclass against testapp, negative-path failure detection, empty-registry and custom-AdminSite edge cases
- `tests/custom_admin_site_urls.py`: URLconf for a non-default-named AdminSite, used by the custom-site test

## Files Modified
- `django_admin_tests/testcases.py`: Replaced stub with full AdminSmokeTestCase implementation (registry iteration, changelist/add assertions, configurable statuses/site/user_factory, @tag)
- `pyproject.toml`: Registered the django_admin_tests pytest marker to silence PytestUnknownMarkWarning

## Decisions
(none)


## Summary

- Work items completed: 1
- Files created: 2
- Files modified: 2
- Tests added: 13
- Coverage: 100%
- Completed: 2026-08-06T21:19:59.176Z
