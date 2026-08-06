---
run: run-django-admin-tests-004
work_item: change-view-instantiation
intent: core-package
mode: validate
checkpoint: plan
approved_at: pending
---

# Implementation Plan: In-house auto-instantiator for change-view testing

Based on approved design document:
`.specs-fire/intents/core-package/work-items/change-view-instantiation-design.md`

## Implementation Checklist

- [ ] `factories.py`: registry dict + `register_factory`/`unregister_factory`/`clear_factories`/`get_factory`, with validation
- [ ] `instantiation.py`: `AdminSmokeWarning`, field→value mapping, `build_instance` with `_building` cycle guard and counter
- [ ] `__init__.py`: re-export `register_factory`, `clear_factories`
- [ ] `testcases.py`: `_reverse_admin_url` gains `args`; `_get_change_view_instance`; `test_admin_smoke_change_view_returns_200`
- [ ] `testapp`: add `SelfReferentialItem` + admin + migration
- [ ] Tests: success path, factory precedence, existing-row reuse, skip+warning path, cycle detection
- [ ] Verify under `pytest` and `manage.py test`; ruff; wheel build

## Files to Create

| File | Purpose |
|------|---------|
| `django_admin_tests/factories.py` | Factory registry + public registration API (no Django imports) |
| `django_admin_tests/instantiation.py` | In-house minimal-instance builder, `AdminSmokeWarning` |
| `testapp/migrations/0002_selfreferentialitem.py` | Migration for the new unbuildable-model fixture |
| `tests/test_factories.py` | Registry tests: registration, precedence, validation, cleanup |
| `tests/test_instantiation.py` | Builder unit tests: field mapping, FK reuse/recursion, cycle detection |

## Files to Modify

| File | Changes |
|------|---------|
| `django_admin_tests/__init__.py` | Re-export `register_factory`, `clear_factories` |
| `django_admin_tests/testcases.py` | `_reverse_admin_url` gains `args`; add `_get_change_view_instance` + `test_admin_smoke_change_view_returns_200` |
| `testapp/models.py` | Add `SelfReferentialItem` (non-null self-FK — unbuildable from empty) |
| `testapp/admin.py` | Register `SelfReferentialItemAdmin` |
| `tests/test_admin_smoke.py` | Change-view success path, factory precedence, skip+warning assertions |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_factories.py` | `register_factory` validation, precedence over auto-build, `clear_factories` isolation |
| `tests/test_instantiation.py` | Per-field-type value mapping, FK reuse vs. recursion, self-reference/cycle raising |
| `tests/test_admin_smoke.py` | End-to-end change-view assertions incl. the skip+warning path for `SelfReferentialItem` |

## Technical Details

Implementation order: `factories.py` (no dependencies) → `instantiation.py`
(depends on nothing but Django) → `__init__.py` re-exports → `testapp`
model + migration → `testcases.py` wiring → tests last.

Global registry state is a leak risk across tests; this repo's own tests
must call `clear_factories()` in teardown (a fixture in
`tests/conftest.py`), and that fixture is itself part of the deliverable.

## Based on Design Doc

Reference: `.specs-fire/intents/core-package/work-items/change-view-instantiation-design.md`

---
This is Checkpoint 2 of Validate mode.
Approve implementation plan? [Y/n/edit]
