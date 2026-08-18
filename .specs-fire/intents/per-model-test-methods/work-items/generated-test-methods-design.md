---
work_item: generated-test-methods
intent: per-model-test-methods
created: 2026-08-18T20:12:19Z
mode: validate
checkpoint_1: approved
---

# Design: Generate one test method per (model, view) pair

## Summary

Replace `AdminSmokeTestCase`'s three registry-looping `subTest` methods with
methods generated at class-creation time by a metaclass — one per
(registered model, view) pair, named
`test_admin_smoke_{app_label}_{model_name}_{view}`.

Registry iteration moves to **class-creation time** (the metaclass reads
`admin_site._registry`); exclusion resolution stays at **run time** (inside each
generated body, via `skipTest`). That split is deliberate: it's what keeps
`@override_settings(ADMIN_TESTS_EXCLUDE=...)` working while still producing
statically-named, individually-addressable tests.

All existing helpers (`_reverse_admin_url`, `_get_admin_view`,
`_get_change_view_instance`, `_allowed_status_codes_for`,
`_assert_allowed_status`) are reused unchanged by the generated bodies.

## Scope

**In Scope:**
- `AdminSmokeMeta` metaclass generating the per-(model, view) methods
- Removal of the three aggregate `subTest` methods (clean break, no aliases)
- Runtime exclusion via `skipTest` inside each generated method
- Neutralizing stale methods inherited by a scope-narrowing subclass
- Empty-registry placeholder method
- Name-collision detection
- Full rewrite of `tests/test_admin_smoke.py` against the new names

**Out of Scope:**
- `tests/test_pytest_plugin.py` assertions and parallel-runner verification —
  that is `runner-compat-verification`
- README / standards / CHANGELOG updates — that is `docs-and-changelog`
- Any change to how instances are built or statuses are resolved

## Verified Facts (prototyped before writing this design)

| Claim | Result |
|-------|--------|
| `type(django.test.TestCase)` is `type` | Confirmed — no metaclass conflict |
| `admin.site._registry` populated when `testcases.py` is imported post-`django.setup()` | Confirmed — all 8 admins present under `tests.settings` |
| `unittest.TestLoader.getTestCaseNames` filters on `callable(getattr(cls, name))` | Confirmed in stdlib source |
| pytest's `UnitTestCase.collect()` uses the *same* `TestLoader().getTestCaseNames()` | Confirmed in `_pytest/unittest.py` |
| Setting an inherited method to `None` on a subclass removes it from **both** runners | Confirmed — prototype subclass collected 0 of 24 inherited |
| `TestCase("name_that_does_not_exist")` raises `ValueError` | Confirmed — constrains the test rewrite |

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Generation mechanism | Metaclass `AdminSmokeMeta` | Fires for the base class *and* every subclass. `__init_subclass__` does not run for the class defining it, so the base `AdminSmokeTestCase` — which `pytest_plugin.py` collects directly — would carry zero tests. No metaclass conflict exists (verified). |
| Method naming | `test_admin_smoke_{app_label}_{model_name}_{view}` | User-chosen. Groups a model's three views together in alphabetical output. Drops `_returns_200`, which was already misleading since allowed status codes are configurable. |
| Neutralizing stale inherited methods | `setattr(cls, name, None)` for tracked names no longer applicable | The only mechanism that works under **both** runners — both funnel through `getTestCaseNames`' `callable()` filter. `__test__ = False` would work for pytest only, silently leaving them live under `manage.py test`. |
| Distinguishing our methods from the host's | Track generated names in a `_admin_smoke_generated` frozenset class attribute | Guarantees we only ever neutralize methods *we* generated. A host project's own `test_*` method on a subclass must never be shadowed. |
| Exclusion timing | Run time, inside the generated body, via `skipTest` | Keeps `@override_settings(ADMIN_TESTS_EXCLUDE=...)` working and keeps exclusions visible as skips. Generation-time exclusion would freeze settings at import. |
| Empty registry | Generate one always-passing `test_admin_smoke_no_registered_admins` placeholder, only when the registry is empty | Preserves today's documented "passes trivially" semantics and stops the class from collecting nothing at all (indistinguishable from "never ran"). Costs nothing when the registry is non-empty — no placeholder is generated at all. |
| Name collisions | Detect at generation time, raise `ImproperlyConfigured` naming both models | Silent coverage loss is the one unacceptable outcome. A loud, actionable import-time error matches Django's own behavior for duplicate app labels. The trigger (app `foo_bar`+model `baz` vs app `foo`+model `bar_baz`) is vanishingly rare. |
| `_smoke_tested_models()` | Split into generation-time iteration and a runtime `_is_excluded(model)` | The method currently fuses registry iteration with exclusion filtering; after this change those happen at two different times and can no longer share one helper. |
| Generated function metadata | Set `__name__`, `__qualname__`, `__doc__` on each | Verbose runners print the docstring's first line; tracebacks and IDs read correctly. |

## Technical Approach

### Generation flow

```
class creation (metaclass __new__)
        │
        ├─ resolve admin_site from namespace or bases
        │
        ├─ registry empty?
        │     └─ yes → generate ONLY test_admin_smoke_no_registered_admins (passes)
        │
        ├─ for model in admin_site._registry:
        │     for view in (changelist, add, change):
        │         build closure → test_admin_smoke_{app}_{model}_{view}
        │
        ├─ collision check: len(generated) != len(registry) * 3
        │     └─ raise ImproperlyConfigured naming the colliding models
        │
        ├─ stale = inherited _admin_smoke_generated - generated
        │     └─ setattr(cls, name, None)   ← removes from BOTH runners
        │
        ├─ setattr(cls, name, fn) for each generated
        └─ cls._admin_smoke_generated = frozenset(generated)
```

### Generated method body (changelist / add)

```
def test(self):
    if self._is_excluded(model):          # runtime — honors @override_settings
        self.skipTest(...)
    url  = self._reverse_admin_url(model, view)
    resp = self._get_admin_view(model, view, url)
    self._assert_allowed_status(model, view, resp)
```

### Generated method body (change)

Identical, plus the preserved skip path: resolve an instance via
`_get_change_view_instance(model)`; if `None`, `warnings.warn(AdminSmokeWarning)`
and `skipTest` rather than fail.

### Subclass narrowing — worked example

`tests/custom_admin_site_urls.custom_admin_site` registers only `Category`.

```
AdminSmokeTestCase           admin.site        → 24 methods (8 models × 3)
  └─ CustomSiteSmokeTest     custom_admin_site →  3 methods (Category × 3)
                                                  ↑ same 3 names, fresh closures
                                                 21 inherited names → None
```

The three `Category` names are *regenerated* (rebound to closures carrying the
custom site's context); the other 21 are shadowed. Collection yields exactly 3.

## Affected Files

| File | Action | Purpose |
|------|--------|---------|
| `django_admin_tests/testcases.py` | Modify | `AdminSmokeMeta`, generated-method factories, `_is_excluded`, placeholder, collision check; remove the three `subTest` methods and `_smoke_tested_models` |
| `tests/test_admin_smoke.py` | Modify | Rewrite all ~12 hand-constructed method names; simplify tests that only looped to reach one model |

## Test Plan

The rewrite mostly *simplifies* this suite — several tests currently do
gymnastics (excluding every model but one) purely to isolate a single model,
which per-model methods make unnecessary.

| Existing test | Rewrite |
|---------------|---------|
| `detects_broken_admin_view` | Break `CategoryAdmin.get_queryset`, run `..._testapp_category_changelist` — now targets the broken admin directly |
| `reports_fieldset_keyerror_clearly` | Run `..._testapp_sluggedarticle_add`; **drops** the `excluded_models = {everything except SluggedArticle}` scaffolding entirely |
| `handles_empty_registry` | Run the placeholder; still asserts `wasSuccessful()` and `testsRun == 1` |
| `supports_custom_admin_site` | Run `..._testapp_category_changelist` on the custom-site subclass; `testsRun == 1` unchanged |
| `change_view_skips_unbuildable_model` | Run `..._testapp_selfreferentialitem_change`; assert skip + `AdminSmokeWarning` |
| `change_view_uses_registered_factory` | Same method, assert not skipped |
| `excluded_models_are_not_smoke_tested` | Retarget from `_smoke_tested_models()` to `_is_excluded()`, plus an end-to-end check that an excluded model's method *skips* |
| Helper-only tests (`_allowed_status_codes_for`, `_get_change_view_instance`, `_reverse_admin_url`, …) | Need a **valid** method name to construct the case (`TestCase(bad)` raises `ValueError`) — use a module-level constant naming one known generated method |

**New tests required:**
- Generated method set matches registry × 3, with exact names
- Base class itself carries generated methods (guards the `__init_subclass__` trap)
- Scope-narrowing subclass collects only its own; inherited names resolve to `None`
- A host-authored `test_*` method on a subclass is **not** shadowed
- Collision detection raises `ImproperlyConfigured` naming both models
- Excluded model's generated method skips, and `@override_settings` toggles it live
- No `subTest` remains; no pytest import in `testcases.py`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Admins registered *after* `testcases.py` is imported get no test — a real behavior regression, since today's loop would catch them at run time | Medium | Registry population happens during app loading, which always precedes test-module import (verified). Document as a limitation in `docs-and-changelog`. |
| A generation error inside the pytest plugin's `try/except` is downgraded to a collection *warning* instead of failing loudly | Medium | Flagged for `runner-compat-verification` to test explicitly; the collision check must not be silently swallowed |
| Import-time cost grows with registry size | Low | Closure creation is O(models × 3) and trivial; NFR is per-admin *request* overhead, untouched |
| `None`-shadowing surprises a host project subclassing twice | Low | Only names in `_admin_smoke_generated` are ever touched; covered by a dedicated test |
| Larger reported test counts alarm users on upgrade | Low | CHANGELOG note in `docs-and-changelog` |
| Pickling for `--parallel` mishandles generated methods | Medium | Deferred by design to `runner-compat-verification`; methods are ordinary class attributes recreated deterministically per worker, so expected to hold |

## Implementation Checklist

- [ ] `AdminSmokeMeta.__new__`: resolve `admin_site`, generate, collision-check, shadow stale, record `_admin_smoke_generated`
- [ ] Method factories for changelist/add and for change (with the preserved skip path), setting `__name__`/`__qualname__`/`__doc__`
- [ ] `_is_excluded(model)` — runtime check against `excluded_models` + `get_excluded_admins()`
- [ ] Empty-registry placeholder `test_admin_smoke_no_registered_admins`
- [ ] Remove the three `subTest` methods and `_smoke_tested_models`
- [ ] Update `AdminSmokeTestCase`'s class docstring (it documents the old behavior)
- [ ] Rewrite `tests/test_admin_smoke.py` per the table above
- [ ] Add the new tests listed above
- [ ] Verify under `pytest` **and** `python -m django test --settings=tests.settings`
- [ ] Confirm `--exclude-tag=django_admin_tests` / `-m "not django_admin_tests"` still exclude everything
- [ ] `ruff check`, `ruff format --check`, coverage ≥ 90% on `django_admin_tests/`

---
*Generated by specs.md - fabriqa.ai FIRE Flow*
