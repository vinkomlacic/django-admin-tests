---
id: per-model-test-methods
title: Per-Model Generated Test Methods (replace subTest)
status: pending
created: 2026-08-18T20:10:26Z
---

# Intent: Per-Model Generated Test Methods (replace subTest)

## Goal

Replace the three `subTest`-looping test methods on `AdminSmokeTestCase` with
dynamically generated test methods — one method per (model, view) pair —
named `test_admin_smoke_<app_label>_<model_name>_<view>`, e.g.
`test_admin_smoke_testapp_product_changelist`.

Today three fat methods each iterate the whole admin registry:

```
test_admin_smoke_changelist_returns_200   → subTest per model
test_admin_smoke_add_view_returns_200     → subTest per model
test_admin_smoke_change_view_returns_200  → subTest per model
```

After this intent, a project with 8 registered admins reports 24 individually
named tests instead of 3.

## Users

- **Host project developers** — the people reading a CI failure and running the
  suite locally. They get a named failing test that identifies the broken admin,
  and can re-run just that one while fixing it.
- **Host project CI systems** — test counts reflect real coverage, and per-model
  tests distribute across parallel workers.
- **This repo's own suite** — dogfoods the same generated methods against
  `testapp`.

## Problem

`subTest` collapses per-model results into three test cases, which causes four
distinct pains (all four were named as motivating):

1. **Failure isolation / reporting.** A broken `ModelAdmin` surfaces as a
   subTest failure buried inside `test_admin_smoke_changelist_returns_200`.
   The model name is in the message, but the *test identity* is the same
   regardless of which admin broke.
2. **Selective re-running.** There is no way to run just one model's checks.
   `pytest -k testapp_product` matches nothing; you re-run all admins to
   iterate on one.
3. **Parallel / distributed runs.** pytest-xdist and Django's `--parallel`
   distribute at test-case granularity, so the entire registry sweep is pinned
   to a single worker — three serial tests no matter how many admins exist.
4. **`subTest` ergonomics.** Reporters and IDEs render subTests inconsistently;
   pytest's handling in particular is awkward.

## Success Criteria

- One test method exists per (registered model, view) pair, named
  `test_admin_smoke_<app_label>_<model_name>_<view>` with `<view>` in
  `changelist` / `add` / `change`.
- No `subTest` remains in `django_admin_tests/testcases.py`.
- Generated methods appear correctly under **both** `manage.py test` and
  `pytest` — including selection by node ID and by `-k` / `pytest -k` substring.
- Subclass customization still works: `admin_site`, `allowed_status_codes`,
  `model_allowed_status_codes`, `excluded_models`, `user_factory`.
- A subclass narrowing scope (e.g. a custom `admin_site`) does **not** inherit
  and run stale methods generated for the parent's registry.
- `ADMIN_TESTS_EXCLUDE` and `excluded_models` still take effect, and still
  respond to `@override_settings` applied at runtime.
- The change-view skip path is preserved: models with no obtainable instance
  emit an `AdminSmokeWarning` and `skipTest`, rather than failing.
- `django_admin_tests/testcases.py` still imports no pytest (hard constraint).
- Coverage on `django_admin_tests/` stays at or above the 90% gate.
- CHANGELOG documents the removal of the three old method names as a breaking
  change.

## Constraints

- **`testcases.py` must never import pytest.** It runs under both
  `manage.py test` and pytest; pytest-native code breaks the former entirely.
  Any pytest-specific glue belongs in `django_admin_tests/pytest_plugin.py`.
  (CLAUDE.md, system-architecture.md, testing-standards.md.)
- **Generation must happen at class-creation time.** unittest and pytest both
  collect test methods as class attributes; there is no lazy hook. Verified
  empirically that `admin.site._registry` is fully populated by the time
  `testcases.py` is imported (i.e. after `django.setup()`), so this is viable —
  but it does mean the registry is read at import time, not at run time.
- **Generation must fire for the base class as well as subclasses.**
  `__init_subclass__` does not run for the class defining it, so the base
  `AdminSmokeTestCase` — which the pytest plugin collects directly — would get
  no methods. A metaclass covers both uniformly.
- **Exclusions resolve at runtime, not at generation time.** Decided: generate a
  method for every registered model and have it call `skipTest` when the model
  is excluded. This keeps `@override_settings(ADMIN_TESTS_EXCLUDE=...)` working
  and keeps exclusions visible as skips in output, at the cost of slightly
  noisier reports.
- **Clean break on the old names.** The three aggregate methods are removed
  outright, not kept as deprecated aliases — retaining them would request every
  admin view twice and roughly double suite runtime. Package is at 0.1.1
  (pre-1.0), so this is acceptable with a CHANGELOG note.
- Per-admin overhead must stay well under a second (existing NFR); generating
  methods must not add meaningful import-time cost for large registries.

## Notes

### Blast radius in this repo

- `tests/test_admin_smoke.py` constructs the old method names by hand in
  roughly a dozen places, e.g.
  `AdminSmokeTest("test_admin_smoke_changelist_returns_200")`. Every one of
  these needs rewriting against generated names.
- `tests/test_pytest_plugin.py:176-190` asserts the three old names appear
  (and don't appear) in pytest stdout.
- `README.md` and `.specs-fire/standards/coding-standards.md` /
  `testing-standards.md` reference the old names as examples.

### Open design questions (for the design doc, not decided here)

1. **Empty registry.** With zero registered admins, zero methods are generated,
   so the class contributes nothing at all — indistinguishable from "the smoke
   tests never ran". Today `test_admin_smoke_changelist_returns_200` passes
   trivially, and
   `tests/test_admin_smoke.py::test_admin_smoke_handles_empty_registry` asserts
   that. Options: accept silence, or emit a single always-present guard test
   that fails/warns when the registry is empty.
2. **Neutralizing inherited methods.** When a subclass regenerates, stale
   methods inherited from the parent must stop being collected. Setting them to
   `None` on the subclass works (unittest's `getTestCaseNames` filters on
   `callable`), but the mechanism should be explicit and tested.
3. **Name collisions.** `f"{app_label}_{model_name}"` is ambiguous in principle:
   app `foo_bar` + model `baz` collides with app `foo` + model `bar_baz`. Rare,
   but a collision would silently drop a model's test. Decide whether to
   disambiguate (e.g. double-underscore separator) or detect and fail loudly.
4. **Method naming drops `_returns_200`.** Chosen deliberately — allowed status
   codes are configurable, so the old suffix was already misleading. Confirm the
   docs stop promising 200 specifically.

---
*Generated by specs.md - fabriqa.ai FIRE Flow*
