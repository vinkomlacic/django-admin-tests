---
run: run-django-admin-tests-008
work_items: [generated-test-methods, runner-compat-verification, docs-and-changelog]
intent: per-model-test-methods
generated: 2026-08-18T20:40:53Z
mode: wide (validate + confirm + autopilot)
---

# Implementation Walkthrough: Per-Model Generated Test Methods

## Summary

`AdminSmokeTestCase` no longer has three methods that loop the admin registry
with `subTest`. It now generates one test method per (registered model, view) at
class-creation time, named `test_admin_smoke_<app_label>_<model_name>_<view>`.

For this repo's own suite that turns 3 collected tests into 24. For a host
project it turns 3 into roughly 3× the number of registered admins, each failing
under its own name and individually re-runnable.

## Structure Overview

The change is concentrated in one module. Everything that does the actual work —
URL reversing, issuing the request, resolving an instance for the change view,
resolving allowed status codes — was already factored into helpers and is reused
untouched. What's new is *when* the registry is read and *how* the methods come
into existence.

```
import time                          run time
─────────────────────────────        ─────────────────────────────
AdminSmokeMeta.__new__               generated method body
  ├─ read admin_site._registry         ├─ _skip_if_excluded(model)   ← settings
  ├─ build one fn per (model, view)    ├─ _reverse_admin_url(...)      read here
  ├─ detect name collisions            ├─ _get_admin_view(...)
  ├─ neutralize stale inherited        └─ _assert_allowed_status(...)
  └─ setattr onto the class
```

That split is the heart of the design: the **method set** is frozen at import,
but the **decision to run** is not. It's why `override_settings(ADMIN_TESTS_EXCLUDE=...)`
still works even though the methods were built long before the test ran.

## Architecture

### Pattern Used

Metaclass-driven test generation, with per-class regeneration on inheritance.

A metaclass rather than `__init_subclass__`, for a concrete reason: that hook
doesn't fire for the class that defines it, so the base `AdminSmokeTestCase`
would carry no tests at all — and the pytest plugin collects that base class
directly. This was verified rather than assumed, and is guarded by
`test_base_class_itself_carries_generated_methods`.

### Inheritance behavior

```
AdminSmokeTestCase         admin.site         → 24 methods
  └─ CustomSiteSmokeTest   custom_admin_site  →  3 methods (Category × 3)
                                                21 inherited names → None
```

A subclass that narrows scope would otherwise inherit closures bound to the
parent's models and resolve their URLs against the wrong site namespace. Stale
names are set to `None`, which removes them from collection under **both**
runners — `unittest.TestLoader.getTestCaseNames` and pytest's
`UnitTestCase.collect` both filter on `callable()`. (`__test__ = False` would
have worked for pytest only, silently leaving them live under `manage.py test`.)

Only names the metaclass generated are ever neutralized, and a method the class
defines itself is never overwritten.

## Files Changed

### Created

| File | Purpose |
|------|---------|
| (none) | |

### Modified

| File | Changes |
|------|---------|
| `django_admin_tests/testcases.py` | `AdminSmokeMeta`, generation helpers, `_is_excluded`/`_skip_if_excluded`, empty-registry placeholder, collision detection; removed the three `subTest` loops and `_smoke_tested_models` |
| `tests/test_admin_smoke.py` | 12 call sites retargeted; 12 tests added |
| `tests/test_pytest_plugin.py` | Assertions retargeted; generation-error test added |
| `CHANGELOG.md` | Breaking-change entry; corrected parallel claim |
| `README.md` | Naming scheme, single-model runs, overrides, 4 new limitations |
| `.specs-fire/standards/coding-standards.md` | Replaced the `subTest` preferred pattern and loop example |
| `.specs-fire/standards/testing-standards.md` | Naming examples, code block, fixed test command |
| `.specs-fire/standards/system-architecture.md` | Component + data-flow descriptions |

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Generation mechanism | Metaclass | Fires for the base class too, which the pytest plugin collects directly |
| Exclusion timing | Run time, inside the generated body | Keeps `@override_settings` working; exclusions stay visible as skips |
| Stale inherited methods | `setattr(cls, name, None)` | The only mechanism both runners honor |
| Host-defined overrides | Skipped during generation, and excluded from the tracked set | A hand-written method is never ours to overwrite or later remove |
| Empty registry | One always-passing placeholder | A class collecting nothing is indistinguishable from "never ran" |
| Name collisions | `ImproperlyConfigured` at import | Silent coverage loss was the one unacceptable outcome |

## What Was Descoped, and Why It Matters

The intent listed four motivations. Three are delivered: failure isolation,
single-model selection, and removing `subTest`.

The fourth — parallel distribution — was **descoped by the user as nice-to-have**
after verification turned up an inconvenient fact: Django's `--parallel`
partitions via `partition_suite_by_case`, which groups by `TestCase` *class*.
All generated methods live on one class, so `len(subsuites) == 1`,
`processes = min(4, 1) = 1`, and the run proceeds serially while reporting
`Ran 24 tests ... OK`. Getting native-runner parallelism would need one TestCase
class per model — a different design.

pytest-xdist distributes per collected item and would benefit, but that was not
verified and no dependency was added.

This is documented as a README limitation, and the CHANGELOG claim that
overstated it was corrected. Worth noting as a process point: that claim was
written in the first work item, *before* the behavior was verified in the
second — the wide-scope run is what caught it.

## Verification

| Path | Result |
|------|--------|
| `pytest tests/` | 113 passed, 1 skipped |
| `python manage.py test tests` | 23 passed, 1 skipped |
| `pytest -k testapp_product` | 3 selected, 108 deselected |
| `manage.py test <node-id>` | 1 test |
| `--exclude-tag` / `-m "not ..."` | 0 tests / 24 deselected |
| Coverage on `testcases.py` | 100% (99% package) |
| `ruff check` + `ruff format --check` | Clean |

## Known Issue Found But Not Introduced

Unscoped `python -m django test --settings=tests.settings` fails with 3 errors —
Django's `test*.py` discovery pattern matches `django_admin_tests/testcases.py`
and runs the un-subclassed base class against `testapp`'s deliberately
permission-denying admin. **Pre-existing on master** (confirmed by stashing the
changes and re-running). CI uses the scoped `python manage.py test tests`, which
is green. `testing-standards.md` documented the broken form; that was corrected.

## Commits

```
7457590  feat(generated-test-methods): one test method per model and view
7c83282  test(runner-compat-verification): pin generated-method selection paths
81bad0c  docs(docs-and-changelog): describe per-model tests, drop subTest guidance
```

Branch: `feat/per-model-test-methods` (not pushed).

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-008*
