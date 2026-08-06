---
run: run-django-admin-tests-004
work_item: change-view-instantiation
intent: core-package
generated: 2026-08-06T21:55:00Z
mode: validate
---

# Implementation Walkthrough: In-house auto-instantiator for change-view testing

## Summary

Change views are now covered. For each registered admin, an instance is
resolved as **registered factory → existing row → auto-built minimal
instance**; if none succeed, the check is skipped with an
`AdminSmokeWarning` naming the model, never failing the suite. The builder
is entirely in-house — the only new imports are stdlib and Django — so no
third-party dependency reaches consumers.

## Structure Overview

Two new modules keep concerns separate. `factories.py` is the public
registration API and holds the module-level registry; it deliberately
imports nothing from Django, which is what makes it safe to re-export from
`__init__.py` without risking app-registry loading order.
`instantiation.py` holds the Django-dependent builder: a field-type →
value mapping, FK resolution, and cycle detection.

`testcases.py` gained a third test method plus `_get_change_view_instance`,
which encodes the resolution order and is the single place that decides
between "test it" and "skip it".

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `django_admin_tests/factories.py` | `register_factory`/`unregister_factory`/`clear_factories`/`get_factory` + the registry dict |
| `django_admin_tests/instantiation.py` | `build_instance`, `value_for_field`, `AdminSmokeWarning`, `InstanceBuildError` |
| `testapp/migrations/0002_selfreferentialitem.py` | Migration for the unbuildable fixture |
| `tests/test_factories.py` | Registry behavior (6 tests) |
| `tests/test_instantiation.py` | Builder behavior (22 tests) |

### Modified

| File | Changes |
|------|---------|
| `django_admin_tests/__init__.py` | Re-exports the registration API |
| `django_admin_tests/testcases.py` | `test_admin_smoke_change_view_returns_200`, `_get_change_view_instance`, `args` on `_reverse_admin_url` |
| `testapp/models.py` | Added `SelfReferentialItem` (required self-FK) |
| `testapp/admin.py` | Registered `SelfReferentialItemAdmin` |
| `tests/conftest.py` | Autouse fixture clearing the registry between tests |
| `tests/test_admin_smoke.py` | Change-view success, skip+warning, factory precedence, resolution order |

## Key Implementation Details

### 1. Grouped `choices` returned an invalid value

`_first_choice` detected grouping by checking whether `choices[0][0]` was a
list/tuple. For Django's grouped form — `[("Group", [(value, label), ...])]`
— it's the *second* slot that holds the nested pairs, so the function
returned the group label `"Group"`, which is not a valid choice and would
fail model validation on any grouped-choice field. Caught by a test written
directly from the design's stated mapping rules; fixed by unpacking
`value, label` and inspecting `label`.

### 2. `USE_TZ = False` projects would have hit datetime warnings

The builder originally produced `datetime.datetime.now(tz=utc)` — always
aware. Django warns when an aware datetime is saved under `USE_TZ = False`
(and vice versa). Since this library runs inside arbitrary host projects it
can't assume either setting, and this repo's own settings use
`USE_TZ = True`, so the bug would never have surfaced locally. Switched to
`django.utils.timezone.now()`, which returns the correct kind for the
active setting.

### 3. An impossible test premise, and what replaced it

An initial test tried to seed a `SelfReferentialItem` with `parent_id=None`
to prove "a self-FK becomes satisfiable once a row exists". That row cannot
exist — the column is `NOT NULL` — so the test failed and poisoned the
surrounding transaction. Removed as unreachable (FK reuse is already
covered elsewhere). The factory test that replaced it uses
`connection.constraint_checks_disabled()` to seed the row, which turns out
to be a genuinely good illustration: that's exactly the model-specific
knowledge the auto-builder cannot have, and precisely why
`register_factory` exists.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Broken *registered* factory | Propagates and fails the test — not caught into skip+warning | A user who explicitly registered a factory wants to know it's broken; auto-builder failure is routine, factory failure is a bug |
| Registry cleanup in this repo's tests | Autouse fixture in `conftest.py` | The registry is global mutable state; without this, one test registering a factory silently alters every later test |
| `isinstance` ordering in `value_for_field` | Most-specific first, with an explanatory comment | `EmailField`/`URLField`/`SlugField` subclass `CharField`; a future reorder would silently break them, so the constraint is documented in place |

## Deviations from Plan

One test from the plan was dropped as unreachable (the self-FK "existing
row" case described above); its intent is covered by
`test_build_instance_reuses_existing_related_row`. Two tests were added
beyond the plan: `test_change_view_instance_resolution_order` (full
three-tier precedence) and grouped-`choices` coverage.

## Dependencies Added

None — the explicit constraint of this work item is upheld.

## How to Verify

1. **Full suite**

   ```bash
   source .venv/bin/activate
   pytest tests/
   ```

   Expected: `45 passed, 1 skipped` — the skip is `SelfReferentialItem`'s
   change view, by design, accompanied by an `AdminSmokeWarning`.

2. **Native runner**

   ```bash
   python manage.py test tests
   ```

   Expected: `Ran 3 tests ... OK (skipped=1)`.

3. **Confirm no new dependencies reached the wheel**

   ```bash
   python -m build --wheel -o /tmp/dab && unzip -l /tmp/dab/*.whl
   ```

   Expected: `factories.py` and `instantiation.py` present; dependency
   metadata still `django>=4.2` only.

## Test Coverage

- Tests added: 45 total in suite (32 new this work item) + 20 subtests
- Coverage: 100% across all three shipped modules
- Status: passing

## Ready for Review

- [x] All acceptance criteria met
- [x] Tests passing
- [x] No critical issues
- [ ] Documentation updated (README still a stub — deferred to `packaging-release-readiness`)
- [x] Developer notes captured

## Developer Notes

- The `AdminSmokeWarning` shows up in this repo's own pytest output. That's
  the feature working, not noise to suppress — it's how a consumer learns a
  model went untested.
- `_needs_value` skips fields with `null=True` or a default, and
  `auto_now`/`auto_now_add` fields. If a consumer reports a model failing to
  build, that predicate is the first place to look.
- The builder makes no attempt to satisfy custom `save()`/`clean()`
  requirements — by design. Those surface as skip+warning, and
  `register_factory` is the documented answer.

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-004*
