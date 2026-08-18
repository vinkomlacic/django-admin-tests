---
id: generated-test-methods
title: Generate one test method per (model, view) pair
intent: per-model-test-methods
complexity: high
mode: validate
status: completed
depends_on: []
created: 2026-08-18T20:12:19Z
run_id: run-django-admin-tests-008
completed_at: 2026-08-18T20:32:51.422Z
---

# Work Item: Generate one test method per (model, view) pair

## Description

Replace the three `subTest`-looping test methods on `AdminSmokeTestCase` with
dynamically generated methods — one per (registered model, view) pair — named
`test_admin_smoke_<app_label>_<model_name>_<view>`, where `<view>` is
`changelist`, `add`, or `change`.

Removed:

```
test_admin_smoke_changelist_returns_200
test_admin_smoke_add_view_returns_200
test_admin_smoke_change_view_returns_200
```

Generated instead (example, `testapp`):

```
test_admin_smoke_testapp_product_changelist
test_admin_smoke_testapp_product_add
test_admin_smoke_testapp_product_change
test_admin_smoke_auth_user_changelist
...
```

Generation happens at class-creation time via a metaclass, so it fires for the
base `AdminSmokeTestCase` (which the pytest plugin collects directly) *and* for
every host-project subclass. The existing helpers (`_reverse_admin_url`,
`_get_admin_view`, `_get_change_view_instance`, `_allowed_status_codes_for`,
`_assert_allowed_status`) are reused unchanged by the generated bodies.

This item includes rewriting this repo's own `tests/test_admin_smoke.py`, which
constructs the old method names by hand in roughly a dozen places — that suite
is what proves the change works.

## Acceptance Criteria

- [ ] One test method exists per (registered model, view) pair, named `test_admin_smoke_<app_label>_<model_name>_<view>`
- [ ] No `subTest` remains anywhere in `django_admin_tests/testcases.py`
- [ ] The three old method names are gone (clean break — no deprecated aliases)
- [ ] Generation fires for the base `AdminSmokeTestCase` itself, not only subclasses
- [ ] A subclass setting `admin_site` to a narrower site does NOT inherit and run methods generated for the parent's registry
- [ ] `excluded_models` and `ADMIN_TESTS_EXCLUDE` are resolved at *runtime* inside each generated method via `skipTest`, so `@override_settings(ADMIN_TESTS_EXCLUDE=...)` still takes effect
- [ ] `allowed_status_codes`, `model_allowed_status_codes` and `user_factory` subclass customization still work, with the documented resolution order (class attr → setting → default)
- [ ] Change-view skip path preserved: a model with no obtainable instance emits `AdminSmokeWarning` and skips, rather than failing
- [ ] `django_admin_tests/testcases.py` imports no pytest
- [ ] Empty-registry behavior matches the design doc's decision, and `tests/test_admin_smoke.py::test_admin_smoke_handles_empty_registry` is updated to assert it
- [ ] Name-collision behavior matches the design doc's decision (disambiguate or fail loudly — not silently drop a model)
- [ ] `tests/test_admin_smoke.py` fully rewritten against generated names; all tests pass
- [ ] Suite passes under both `pytest` and `python -m django test --settings=tests.settings`
- [ ] Coverage on `django_admin_tests/` stays at or above the 90% gate
- [ ] `ruff check` and `ruff format --check` pass

## Technical Notes

**Why a metaclass, not `__init_subclass__`.** `__init_subclass__` does not run
for the class that defines it, so the base `AdminSmokeTestCase` would end up
with zero test methods. The pytest plugin
(`django_admin_tests/pytest_plugin.py`) collects the `testcases` module
directly and relies on the base class carrying the tests, so this is not a
theoretical gap. Django's `TestCase` has no custom metaclass, so there is no
metaclass conflict to resolve.

**Stale inherited methods.** A subclass narrowing scope — e.g.
`class MySmoke(AdminSmokeTestCase): admin_site = my_site` — inherits every
method the base generated for `admin.site`. Those closures capture the parent's
models, and `_reverse_admin_url` would resolve them against
`self.admin_site.name` (the *custom* site), producing spurious failures. On
regeneration, inherited-but-inapplicable names must be neutralized. Setting
them to `None` on the subclass works because unittest's `getTestCaseNames`
filters on `callable(getattr(cls, name))`. Track generated names in a class
attribute so regeneration knows what to clear. This mechanism needs its own
test.

**Registry timing — verified.** `admin.site._registry` is fully populated by
the time `django_admin_tests/testcases.py` is imported, provided the import
happens after `django.setup()` (confirmed empirically against
`tests.settings`: all 8 admins present at import time). Test modules are
always imported post-setup by both runners, so class-creation-time generation
is sound. Note the consequence: the *registry* is read at import time even
though *exclusions* are read at run time.

**Runtime exclusion.** `_smoke_tested_models()` currently fuses two concerns:
registry iteration and exclusion filtering. Generation needs the former;
the generated body needs the latter. Split accordingly rather than calling
`_smoke_tested_models()` from both places.

**Naming.** `app_label` and `model_name` are both valid Python identifiers by
Django's own rules, so no sanitization is needed — but `f"{app_label}_{model_name}"`
is ambiguous (app `foo_bar` + model `baz` vs app `foo` + model `bar_baz`).
See the design doc.

**Open questions to resolve in the design doc** (from the intent brief):
1. Empty registry → zero methods → class silently contributes nothing. Accept, or emit a guard test?
2. Exact mechanism and test for neutralizing inherited methods.
3. Name-collision handling.
4. Dropping `_returns_200` from method names — confirm docs stop promising 200 specifically.

**Files expected to change**: `django_admin_tests/testcases.py` (core),
`tests/test_admin_smoke.py` (~12 call sites).

## Dependencies

(none)
