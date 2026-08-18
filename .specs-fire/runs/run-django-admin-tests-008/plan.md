---
run: run-django-admin-tests-008
work_item: generated-test-methods
intent: per-model-test-methods
mode: validate
checkpoint: plan
approved_at: 2026-08-18T20:19:29Z
---

# Implementation Plan: Generate one test method per (model, view) pair

## Approach

Add an `AdminSmokeMeta` metaclass to `django_admin_tests/testcases.py` that, at
class-creation time, reads `cls.admin_site._registry` and binds one test method
per (model, view) pair onto the class. Remove the three `subTest` loops.

The existing helpers do all the real work already — the generated bodies are
thin wrappers over `_reverse_admin_url`, `_get_admin_view`,
`_get_change_view_instance` and `_assert_allowed_status`. The only behavioral
helper change is splitting `_smoke_tested_models()`: registry iteration moves
into the metaclass (class-creation time), exclusion becomes `_is_excluded()` /
`_skip_if_excluded()` (run time).

### Metaclass

```python
class AdminSmokeMeta(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        admin_site = getattr(cls, "admin_site", None)
        if admin_site is None:
            return cls

        generated = _build_generated_tests(admin_site)      # name -> function
        inherited = getattr(cls, "_admin_smoke_generated", frozenset())

        for stale in inherited - generated.keys():
            setattr(cls, stale, None)                        # drops from BOTH runners
        for method_name, method in generated.items():
            setattr(cls, method_name, method)

        cls._admin_smoke_generated = frozenset(generated)
        return cls
```

`_admin_smoke_generated` is read via `getattr` off the freshly built class, so
it picks up the *inherited* value from bases — which is exactly the set that may
need neutralizing. It is then overwritten with this class's own set.

### Name building and collision detection

```python
def _generated_method_name(model, view_name):
    opts = model._meta
    return f"test_admin_smoke_{opts.app_label}_{opts.model_name}_{view_name}"
```

`_build_generated_tests` accumulates `name -> (model, function)`. If a name is
already claimed by a *different* model, raise `ImproperlyConfigured` naming both
models and pointing at `ADMIN_TESTS_EXCLUDE` as the escape hatch.

### Generated bodies

```python
# changelist / add
def test(self):
    self._skip_if_excluded(model)
    url = self._reverse_admin_url(model, view_name)
    response = self._get_admin_view(model, view_name, url)
    self._assert_allowed_status(model, view_name, response)

# change — preserves the skip path verbatim
def test(self):
    self._skip_if_excluded(model)
    instance = self._get_change_view_instance(model)
    if instance is None:
        message = (...)                       # unchanged wording
        warnings.warn(message, AdminSmokeWarning, stacklevel=2)
        self.skipTest(message)
    url = self._reverse_admin_url(model, "change", args=[instance.pk])
    response = self._get_admin_view(model, "change", url)
    self._assert_allowed_status(model, "change", response)
```

Each function gets `__name__`, `__qualname__` and a `__doc__` of the form
`"{model._meta.label} {view} view returns an allowed status code."`

### Empty registry

When `admin_site._registry` is empty, `_build_generated_tests` returns exactly
one entry: `test_admin_smoke_no_registered_admins`, an always-passing method.
Because it lives in `_admin_smoke_generated` like any other, a subclass that
moves from an empty site to a populated one has it neutralized automatically.

## Files to Create

| File | Purpose |
|------|---------|
| (none) | |

## Files to Modify

| File | Changes |
|------|---------|
| `django_admin_tests/testcases.py` | Add `AdminSmokeMeta`, `_generated_method_name`, `_build_generated_tests`, method factories, `_is_excluded`, `_skip_if_excluded`; remove the three `subTest` methods and `_smoke_tested_models`; update the class docstring |
| `tests/test_admin_smoke.py` | Rewrite ~12 hand-constructed method names; drop now-unnecessary isolation scaffolding; add the new generation tests |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_admin_smoke.py` | Generated-name set matches registry × 3; base class carries methods; scope-narrowing subclass collects only its own (inherited resolve to `None`); host-authored `test_*` not shadowed; collision raises `ImproperlyConfigured`; exclusion skips at runtime and responds to `@override_settings`; change-view skip + warning preserved; all existing behavior retargeted |

## Technical Details

### Existing tests — rewrite mapping

| Existing test | Change |
|---------------|--------|
| `detects_broken_admin_view` | Run `..._testapp_category_changelist` — targets the broken admin directly |
| `reports_fieldset_keyerror_clearly` | Run `..._testapp_sluggedarticle_add`; **delete** the `excluded_models = {all but SluggedArticle}` scaffolding |
| `handles_empty_registry` | Run the placeholder; keeps `wasSuccessful()` + `testsRun == 1` |
| `supports_custom_admin_site` | Run `..._testapp_category_changelist` on the custom-site subclass; `testsRun == 1` |
| `change_view_skips_unbuildable_model` | Run `..._testapp_selfreferentialitem_change` |
| `change_view_uses_registered_factory` | Same method; assert not skipped |
| `excluded_models_are_not_smoke_tested` | Retarget `_smoke_tested_models()` → `_is_excluded()`, plus end-to-end skip assertion |
| Helper-only tests | `TestCase("bad name")` raises `ValueError`, so these need a real generated name — module-level constant |

### Constraints carried into implementation

- No pytest import in `testcases.py` (CLAUDE.md, coding-standards.md)
- `@tag("django_admin_tests")` stays on the class; generated methods inherit it,
  so `--exclude-tag` / `-m "not django_admin_tests"` must still exclude everything
- Import order: stdlib → third-party → local
- ruff format, line length 88

### Scope note discovered during planning

`coding-standards.md` promotes `self.subTest(model=model)` as a **Preferred
Pattern** (lines 173-175) and its Error Handling example (lines 108-121) is
built on the registry loop. Both become anti-patterns after this work item.
`docs-and-changelog` will be widened to cover them — recorded here so it isn't
lost between items.

## Based on Design Doc

Reference: `.specs-fire/intents/per-model-test-methods/work-items/generated-test-methods-design.md`

---
*Plan approved at checkpoint. Execution follows.*

---

## Work Item: runner-compat-verification

### Pre-plan investigation (already run, not assumed)

| Path | Result |
|------|--------|
| pytest plugin auto-collection | ✅ Works — host project gets 15 injected tests (13 passed, 3 skipped), no host imports |
| `manage.py test` node-ID selection | ✅ Works — `tests.test_admin_smoke.AdminSmokeTest.test_admin_smoke_testapp_product_changelist` runs 1 test |
| `pytest -k <app>_<model>` | ✅ Works — `-k testapp_product` selects exactly 3, deselects 108 |
| Django `--parallel` | ❌ **Does not distribute per method** — see below |
| pytest-xdist | ⚠️ Unverified — not installed, not in dev deps |

### Finding: Django's `--parallel` gives no benefit here

`DiscoverRunner.build_suite` partitions with `partition_suite_by_case`, which is
`groupby(all_tests, type)` — it groups by **TestCase class**, not by test method:

```python
subsuites = partition_suite_by_case(suite)
processes = min(self.parallel, len(subsuites))
if processes > 1:
    suite = self.parallel_test_suite(...)
```

All generated methods live on a single class, so `len(subsuites) == 1`,
`processes = min(4, 1) = 1`, and the run silently proceeds serially.
`manage.py test tests --parallel 4` reports `Ran 24 tests ... OK` while using one
process.

This does not break anything — it means motivation #3 from the intent brief is
delivered for pytest-xdist (which distributes per collected *item*) but **not**
for Django's native runner. Getting Django-side parallelism would require one
TestCase *class* per model, a materially different design from the one approved.

### Scope decision (user, at checkpoint)

**Parallelism is dropped from this work item** — the user classified it as
nice-to-have rather than a requirement. No pytest-xdist dependency, no CI
parallel cell, no test asserting the partitioning behavior.

Two consequences carried into `docs-and-changelog`:

- The `[Unreleased]` CHANGELOG entry written in the previous work item claims
  the per-model tests "distribute across parallel workers". That is true for
  pytest-xdist but **not** for `manage.py test --parallel`. The wording must be
  corrected so the package doesn't advertise a benefit its own native runner
  doesn't deliver.
- README should not claim parallel distribution either.

### Approach

Verification only — no production code changes expected.

1. Lock in the three verified paths as regression tests, so they can't silently
   break later.
2. Confirm a generation error inside the plugin isn't downgraded to a warning
   (flagged in the design doc's risk table).

### Files to Modify

| File | Changes |
|------|---------|
| `tests/test_pytest_plugin.py` | Assert a generation-time `ImproperlyConfigured` surfaces rather than being swallowed by the collection `try/except` |
| `tests/test_admin_smoke.py` | Selection regression tests: node-ID addressability, `-k` substring granularity |

### Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_admin_smoke.py` | One generated method is individually addressable by node ID; `-k <app>_<model>` selects exactly that model's three tests |
| `tests/test_pytest_plugin.py` | Generated names collected under auto-collection; collision error not silently swallowed |
