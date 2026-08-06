---
run: run-django-admin-tests-004
work_item: change-view-instantiation
intent: core-package
generated: 2026-08-06T21:45:00Z
status: passed
---

# Test Report: In-house auto-instantiator for change-view testing

## Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit | 34 | 0 | 0 | 100% |
| Integration | 11 | 0 | 1 | 100% |
| **Total** | 45 | 0 | 1 | 100% |

(13 tests carried over from previous work items; 32 new this work item,
plus 20 `subTest` assertions. The 1 skip is `SelfReferentialItem`'s
change view — the deliberate skip+warning path working as designed, not a
gap.)

## Acceptance Criteria Validation

- ✅ **In-house instantiator fills required fields with type-appropriate naive defaults** — 12 parametrized field-type tests in `tests/test_instantiation.py` cover Char/Text/Slug/Integer/Boolean/Date/DateTime/Time/Duration/UUID/JSON/Binary, plus Email shape, `max_length` truncation, `choices` precedence (flat and grouped), and unique-integer counters
- ✅ **No third-party dependency introduced for instantiation** — `instantiation.py` imports only stdlib (`datetime`, `itertools`, `uuid`) and `django.db.models`; `pyproject.toml` dependencies unchanged
- ✅ **`register_factory(Model, callable)` registry exists; registered factories take precedence** — `tests/test_factories.py` (6 tests) plus `test_change_view_instance_resolution_order`, which asserts the full factory → existing row → auto-build ordering
- ✅ **Change view requested against the instance; status asserted against allowed statuses** — `test_admin_smoke_change_view_returns_200` runs against all 5 testapp admins, including the 403 override for `RestrictedItem`
- ✅ **Failed instantiation → skipped (not failed) + warning identifying the model** — `test_admin_smoke_change_view_skips_unbuildable_model` asserts both the recorded skip and the `AdminSmokeWarning` naming `SelfReferentialItem`
- ✅ **testapp's empty-table / complex-FK models exercise both success and skip paths** — `EmptyOnlyModel` (builds from empty), `Product` (FK resolution + existing-row reuse), `SelfReferentialItem` (skip+warning)
- ✅ **No pytest import in testcases.py** — existing `test_testcases_module_never_imports_pytest` still passing against the extended implementation

## Tests Written

### Unit Tests

- `tests/test_factories.py` — 6 tests: register/get, unregistered returns None, non-callable rejection, unregister, clear, package-root export
- `tests/test_instantiation.py` — 22 tests: plain build, FK fill, existing-row reuse, build-from-empty, circular-FK raising, 12 parametrized field types, `max_length` truncation, flat and grouped `choices`, email shape, unique-integer counter

### Integration Tests

- `tests/test_admin_smoke.py::AdminSmokeTest::test_admin_smoke_change_view_returns_200` — change views for all 5 registered admins
- `tests/test_admin_smoke.py::test_admin_smoke_change_view_skips_unbuildable_model` — skip + warning path
- `tests/test_admin_smoke.py::test_admin_smoke_change_view_uses_registered_factory` — a factory rescues an otherwise-skipped model
- `tests/test_admin_smoke.py::test_change_view_instance_resolution_order` — factory > existing row > auto-build

## Test Commands

```bash
pytest tests/
python manage.py test tests
python manage.py test tests --exclude-tag=django_admin_tests
pytest tests/ --cov=django_admin_tests --cov-report=term-missing
```

## Coverage Details

| Module | Statements | Branches | Functions | Lines |
|--------|------------|----------|-----------|-------|
| `django_admin_tests/factories.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/instantiation.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/testcases.py` | 100% | 100% | 100% | 100% |

## Issues Found

Two bugs found by the new tests and fixed before completion (none left open).

**1. Grouped `choices` returned the group label instead of a valid value.**
`_first_choice` checked whether `choices[0][0]` was a list/tuple to detect
grouping, but for `[("Group", [(value, label), ...])]` it's the *second*
slot that holds the nested pairs. The function returned `"Group"` — not a
valid choice — which would have failed model validation on any grouped-choice
field. Fixed to unpack `value, label` and inspect `label`.

**2. Test premise was impossible (test bug, not product bug).**
An initial test tried to seed a `SelfReferentialItem` via
`parent_id=None` to prove "a self-FK is satisfiable once a row exists".
That row cannot exist — the column is `NOT NULL` — so the test failed with
an `IntegrityError` and, worse, poisoned the surrounding transaction.
Removed: the scenario is unreachable, and FK-reuse is already covered by
`test_build_instance_reuses_existing_related_row`. The related
factory-based test was reworked to use
`connection.constraint_checks_disabled()`, which is exactly the
model-specific knowledge the auto-builder can't have — making it a
realistic demonstration of why `register_factory` exists.

## Ready for Completion

- [x] All tests passing
- [x] Coverage target met (100%, exceeds the 90% requirement)
- [x] All acceptance criteria validated
- [x] No critical issues open

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-004*
