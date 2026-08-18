---
run: run-django-admin-tests-008
work_item: generated-test-methods
intent: per-model-test-methods
generated: 2026-08-18T20:19:29Z
status: passing
---

# Test Report: Generate one test method per (model, view) pair

## Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| pytest (`pytest tests/`) | 109 | 0 | 1 | 100% |
| Django runner (`manage.py test tests`) | 23 | 0 | 1 | — |
| **Total** | **109** | **0** | **1** | **100%** |

The single skip is `testapp.SelfReferentialItem`'s change view — the
deliberately-unbuildable fixture proving the skip-with-warning path survived.

`django_admin_tests/testcases.py`: **100%** (140/140 statements).
Package total: 98%, against a 90% gate.

Test counts rose because the change is doing its job: `manage.py test tests`
went from 3 collected tests to 24 (8 registered models × 3 views), and the
pytest plugin's end-to-end host project from 3 injected tests to 15.

## Acceptance Criteria Validation

- ✅ **One method per (registered model, view), named `test_admin_smoke_<app>_<model>_<view>`** — `test_one_method_is_generated_per_model_and_view` asserts the collected set equals registry × views exactly
- ✅ **No `subTest` remains in `testcases.py`** — verified by grep; all three loops removed
- ✅ **Three old method names gone (clean break)** — no aliases retained
- ✅ **Generation fires for the base class itself** — `test_base_class_itself_carries_generated_methods` guards the `__init_subclass__` trap directly
- ✅ **Scope-narrowing subclass doesn't inherit stale methods** — `test_narrowing_subclass_drops_methods_inherited_from_the_parent_site` asserts 3 collected (not 24) and that a parent-only name resolves to `None`
- ✅ **Exclusions resolve at runtime; `@override_settings` still works** — `test_settings_exclusion_applies_without_regenerating_methods` proves the method set is frozen at import while the decision to run is not
- ✅ **`allowed_status_codes`/`model_allowed_status_codes`/`user_factory` still work** — existing resolution-order tests retargeted and passing
- ✅ **Change-view skip path preserved** — `test_admin_smoke_change_view_skips_unbuildable_model` asserts both the skip and the `AdminSmokeWarning`
- ✅ **No pytest import in `testcases.py`** — grep for `^\s*(import|from).*pytest` returns nothing
- ✅ **Empty-registry behavior matches design** — `test_admin_smoke_handles_empty_registry` asserts the placeholder is the only collected method, still `testsRun == 1`
- ✅ **Collisions never silently drop a model** — `test_colliding_generated_names_raise_rather_than_dropping_a_model` asserts `ImproperlyConfigured`
- ✅ **`tests/test_admin_smoke.py` rewritten; all tests pass** — 12 call sites retargeted, 7 tests added
- ✅ **Passes under both runners** — `pytest tests/` and `python manage.py test tests`
- ✅ **Coverage ≥ 90% on `django_admin_tests/`** — 100% on the changed module
- ✅ **`ruff check` / `ruff format --check` pass** — clean

## Tests Written

### Generation (new)

- `tests/test_admin_smoke.py` — `test_one_method_is_generated_per_model_and_view`: collected set equals registry × views
- `tests/test_admin_smoke.py` — `test_base_class_itself_carries_generated_methods`: guards the metaclass-vs-`__init_subclass__` decision
- `tests/test_admin_smoke.py` — `test_generated_methods_are_named_and_documented`: `__name__`, `__qualname__`, `__doc__`
- `tests/test_admin_smoke.py` — `test_narrowing_subclass_drops_methods_inherited_from_the_parent_site`: the `None`-shadowing mechanism
- `tests/test_admin_smoke.py` — `test_host_authored_test_methods_are_never_shadowed`: we only neutralize what we generated
- `tests/test_admin_smoke.py` — `test_metaclass_generates_nothing_without_an_admin_site`: the inert guard
- `tests/test_admin_smoke.py` — `test_colliding_generated_names_raise_rather_than_dropping_a_model`: `ImproperlyConfigured` on ambiguous names

### Exclusion (new / retargeted)

- `test_excluded_models_are_not_smoke_tested` — retargeted from `_smoke_tested_models()` to `_is_excluded()`
- `test_excluded_model_reports_as_skipped_rather_than_vanishing` — the method still exists and skips
- `test_settings_exclusion_applies_without_regenerating_methods` — the load-bearing test for the runtime-exclusion design decision

### Retargeted (behavior unchanged)

- `detects_broken_admin_view`, `reports_fieldset_keyerror_clearly`, `handles_empty_registry`, `supports_custom_admin_site`, `change_view_skips_unbuildable_model`, `change_view_uses_registered_factory`, and the helper-level tests

## Test Commands

```bash
# Run all tests
pytest tests/
python manage.py test tests

# Run with coverage
coverage run -m pytest tests/ && coverage report --include="django_admin_tests/*"

# Runner-exclusion paths
python manage.py test tests --exclude-tag=django_admin_tests   # -> 0 tests
pytest tests/ -m "not django_admin_tests"                      # -> 24 deselected
```

## Coverage Details

| Module | Statements | Missing | Cover |
|--------|------------|---------|-------|
| `django_admin_tests/testcases.py` | 140 | 0 | 100% |
| `django_admin_tests/instantiation.py` | 93 | 0 | 100% |
| `django_admin_tests/settings.py` | 38 | 0 | 100% |
| `django_admin_tests/pytest_plugin.py` | 28 | 2 | 93% |
| `django_admin_tests/factories.py` | 11 | 0 | 100% |
| **Total** | **322** | **5** | **98%** |

## Issues Found

| Issue | Severity | Status |
|-------|----------|--------|
| `tests/test_pytest_plugin.py` asserted the three removed method names | Medium | Fixed here — assertions retargeted to generated names and to `passed=13, skipped=3`. Deeper plugin/parallel verification remains `runner-compat-verification`'s scope |
| Unscoped `python -m django test --settings=tests.settings` fails with 3 errors | Low | **Pre-existing on master**, not caused by this work item. Django's `test*.py` discovery pattern matches `django_admin_tests/testcases.py` and runs the un-subclassed base class, which correctly fails on `RestrictedItem`'s deliberate 403. CI runs the scoped `python manage.py test tests`, which is green. `testing-standards.md:96` documents the broken unscoped form — logged for `docs-and-changelog` |

## Ready for Completion

- [x] All tests passing
- [x] Coverage target met (90%)
- [x] All acceptance criteria validated
- [x] No critical issues open

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-008*

---

## Work Item: runner-compat-verification

### Test Results

- Passed: 113 (pytest), 23 (Django runner)
- Failed: 0
- Skipped: 1 (the `SelfReferentialItem` change-view fixture)

No production code changed — this item is verification only. Coverage on
`django_admin_tests/` unchanged at 98% (100% on `testcases.py`).

### Verification Matrix

| Path | Verified | How |
|------|----------|-----|
| pytest plugin auto-collection surfaces generated names | ✅ | `test_auto_collection_runs_smoke_tests_with_no_host_imports` — 15 injected tests in a host project that never imports the package |
| Auto-collection stays off by default | ✅ | `test_no_auto_collection_when_ini_flag_is_off` — retargeted to a generated name |
| `manage.py test <dotted.path>` selects one generated method | ✅ | `test_generated_method_is_addressable_by_node_id` via `loadTestsFromName`, the mechanism behind node-ID selection |
| `pytest -k <app>_<model>` selects exactly that model | ✅ | `test_model_substring_selects_exactly_that_models_tests`; confirmed live: `-k testapp_product` → 3 selected, 108 deselected |
| Generation error doesn't abort the host's session | ✅ | `test_generation_error_warns_instead_of_aborting_collection` |
| `--exclude-tag` / `-m "not django_admin_tests"` | ✅ | 0 tests and 24 deselected respectively |
| Parallel distribution | ⬜ | **Descoped by the user** — nice-to-have, not a requirement |

### Acceptance Criteria Validation

Criteria are validated against the **descoped** work item — the four
parallelism-related criteria were dropped at the checkpoint.

- ✅ **`tests/test_pytest_plugin.py` updated to assert generated method names** — both the enabled and disabled paths
- ✅ **Node-ID selection under `manage.py test`** — covered by test, plus a live run selecting 1 of 24
- ✅ **`pytest -k <app>_<model>` selects exactly that model's tests** — covered by test and live run
- ✅ **Test counts correct** — 8 models × 3 views = 24 on the dogfood class; host project 5 × 3 = 15
- ✅ **Generation error not silently downgraded past a warning** — behavior now encoded in a test
- ⬜ **Parallel (`--parallel`, xdist)** — descoped
- ✅ **Full suite passes under both runners** — 113 pytest, 23 Django
- ✅ **`ruff check` / `ruff format --check`** — clean

### Finding: Django's `--parallel` does not distribute per method

Recorded here because it outlives this work item even though verification was
descoped.

`DiscoverRunner.build_suite` partitions via `partition_suite_by_case`, which is
`groupby(all_tests, type)` — grouping by TestCase **class**. All generated
methods live on one class, so `len(subsuites) == 1` and
`processes = min(parallel, 1) = 1`. `manage.py test tests --parallel 4` reports
`Ran 24 tests ... OK` while running in a single process.

pytest-xdist distributes per collected *item* and would benefit, but this was
not verified (no dependency added, per the checkpoint decision).

**Consequence for `docs-and-changelog`**: the `[Unreleased]` CHANGELOG entry
committed with the previous work item claims the tests "distribute across
parallel workers". That must be corrected — it is not true for the native
runner, and unverified for xdist.

### Issues Found

| Issue | Severity | Status |
|-------|----------|--------|
| CHANGELOG overstates parallel distribution | Medium | Open — assigned to `docs-and-changelog` |
| A name collision yields zero smoke tests plus a warning under the pytest plugin | Low | Documented by test; behavior matches the plugin's existing "never abort the host's run" philosophy. Not changed |

---

## Work Item: docs-and-changelog

### Test Results

- Passed: 113 (pytest), 23 (Django runner)
- Failed: 0
- Skipped: 1

Documentation-only work item — no code changed, so the suite is unchanged.
Verification here is that the *documented commands* actually work and that no
stale references survive.

### Acceptance Criteria Validation

- ✅ **CHANGELOG documents the removal as a breaking change** — `[Unreleased]` names all three removed methods, the new scheme, the node-ID migration note, and the rise in reported test counts
- ✅ **CHANGELOG no longer overstates parallelism** — the "distribute across parallel workers" claim was corrected to node-ID / `-k` selection, which is what actually holds
- ✅ **README reflects per-model tests** — new naming block near the top, a "Running one model's tests" section, and the single-model override documented
- ✅ **README documents individual selectability** — both `pytest -k` and the `manage.py test` node-ID form
- ✅ **README no longer promises 200 where configurable** — exclusions documented as *skips*, and the four new limitations spell out the actual guarantees
- ✅ **`coding-standards.md:39` naming example updated** — plus a second row for the generated-method pattern
- ✅ **`coding-standards.md` "Per-admin subtests" preferred pattern replaced** — now "One generated test method per admin", with the reason `subTest` was dropped
- ✅ **`coding-standards.md` Error Handling example updated** — the loop-based sample replaced with the generator, noting the test *name* carries the model too
- ✅ **`testing-standards.md:42` example updated** — and the shipped-code pattern documented separately from this repo's own conventions
- ✅ **`testing-standards.md` illustrative code block updated** — shows the metaclass, including why not `__init_subclass__`
- ✅ **`system-architecture.md` updated** — component purpose/responsibilities and the data-flow steps now describe generation at class-creation time with runtime exclusion
- ✅ **No stale references outside historical records** — remaining matches are the CHANGELOG naming what it removed and coding-standards explaining why `subTest` is gone, both intentional

### Beyond the original scope

Three things were folded in that the work item didn't originally list, because
they were discovered during the earlier items:

1. `coding-standards.md`'s "Per-admin subtests" **Preferred Pattern** and its
   Error Handling example — both actively recommended the approach this intent
   removed.
2. The CHANGELOG parallelism correction.
3. `testing-standards.md`'s documented test command
   (`python -m django test --settings=tests.settings`), which **fails**: Django's
   `test*.py` discovery matches `django_admin_tests/testcases.py` and runs the
   un-subclassed base class against `testapp`'s permission-denying admin. Now
   documents the scoped `python manage.py test tests` that CI actually uses,
   with a comment explaining why scoping matters. Pre-existing bug on master,
   fixed here since the file was being touched anyway — and verified to work.

### Issues Found

No open issues. The two carried in from earlier items are resolved: the
CHANGELOG parallel claim is corrected, and the stale test command is fixed.
