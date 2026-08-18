---
id: run-django-admin-tests-008
scope: wide
work_items:
  - id: generated-test-methods
    intent: per-model-test-methods
    mode: validate
    status: completed
    current_phase: review
    checkpoint_state: approved
    current_checkpoint: plan
  - id: runner-compat-verification
    intent: per-model-test-methods
    mode: confirm
    status: completed
    current_phase: review
    checkpoint_state: approved
    current_checkpoint: plan
  - id: docs-and-changelog
    intent: per-model-test-methods
    mode: autopilot
    status: completed
    current_phase: review
    checkpoint_state: none
    current_checkpoint: null
current_item: null
status: completed
started: 2026-08-18T20:19:29.139Z
completed: 2026-08-18T20:40:53.069Z
---

# Run: run-django-admin-tests-008

## Scope
wide (3 work items)

## Work Items
1. **generated-test-methods** (validate) — completed
2. **runner-compat-verification** (confirm) — completed
3. **docs-and-changelog** (autopilot) — completed


## Current Item
(all completed)

## Files Created
(none)

## Files Modified
- `django_admin_tests/testcases.py`: AdminSmokeMeta metaclass generating one test method per (model, view); runtime exclusion via _is_excluded/_skip_if_excluded; empty-registry placeholder; collision detection; removed the three subTest loops and _smoke_tested_models
- `tests/test_admin_smoke.py`: Rewrote 12 call sites against generated names; added 12 tests covering generation, shadowing, overrides, collisions and selection
- `tests/test_pytest_plugin.py`: Retargeted assertions to generated names; added a test that a generation-time ImproperlyConfigured warns rather than aborting the host session
- `CHANGELOG.md`: Breaking-change entry for the removed method names; corrected the parallel-distribution claim
- `README.md`: Generated naming scheme, running one model, single-model override, four new known limitations
- `.specs-fire/standards/coding-standards.md`: Replaced the subTest preferred pattern and loop-based error-handling example; added the generated-name convention
- `.specs-fire/standards/testing-standards.md`: Updated naming examples and illustrative code block; fixed the documented test command
- `.specs-fire/standards/system-architecture.md`: Component and data-flow descriptions now reflect class-creation-time generation

## Decisions
(none)


## Summary

- Work items completed: 3
- Files created: 0
- Files modified: 8
- Tests added: 19
- Coverage: 99%
- Completed: 2026-08-18T20:40:53.069Z
