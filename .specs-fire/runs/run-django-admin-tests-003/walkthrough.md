---
run: run-django-admin-tests-003
work_item: admin-smoke-testcase-core
intent: core-package
generated: 2026-08-06T21:35:00Z
mode: validate
---

# Implementation Walkthrough: AdminSmokeTestCase core (changelist + add views)

## Summary

Implemented `AdminSmokeTestCase` — the library's headline feature. It
iterates every `ModelAdmin` registered on a configurable `AdminSite`, logs
in as a disposable superuser, and asserts each admin's changelist and add
views return an allowed status (default `{200}`, overridable globally or
per-model). Ships with zero pytest dependency, is excludable via
`--exclude-tag=django_admin_tests`, and is proven — by a negative-path
test — to actually catch a broken admin rather than merely pass.

## Structure Overview

`django_admin_tests/testcases.py` went from a docstring-only stub to the
full implementation. Everything is driven off class attributes so host
projects customize by subclassing rather than by configuration files:
`admin_site`, `allowed_status_codes`, `model_allowed_status_codes`, and
`user_factory`. Two private helpers do the work —`_reverse_admin_url`
(namespace-aware URL resolution via `admin_site.name`) and
`_assert_allowed_status` (per-model override lookup + a failure message
naming the offending model and view) — and the two public test methods are
thin loops over the registry wrapped in `subTest`.

`tests/test_admin_smoke.py` dogfoods it against `testapp` and covers the
edge cases `testing-standards.md` requires: an empty registry, and a
custom non-default-named `AdminSite` (backed by its own URLconf in
`tests/custom_admin_site_urls.py`).

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `tests/test_admin_smoke.py` | Dogfood subclass against `testapp` (incl. the `RestrictedItem` 403 override), negative-path failure-detection test, empty-registry and custom-`AdminSite` edge cases |
| `tests/custom_admin_site_urls.py` | URLconf exposing a non-default-named `AdminSite`, so the custom-site test has real URLs to resolve |

### Modified

| File | Changes |
|------|---------|
| `django_admin_tests/testcases.py` | Stub → full `AdminSmokeTestCase` implementation |
| `pyproject.toml` | Registered the `django_admin_tests` pytest marker (silences `PytestUnknownMarkWarning`) |

## Key Implementation Details

### 1. The negative-path test was passing vacuously — the most important find

The test that proves "a broken admin actually fails the suite" drove the
case via `case.run(result)`. Django's `SimpleTestCase` does its per-test
setup — including creating `self.client` — in `_pre_setup`, which is
invoked by `__call__`, **not** by `run`. So the case errored out on a
missing `client` attribute long before touching the broken admin, and
`assert not result.wasSuccessful()` passed for entirely the wrong reason.
It would have kept passing even if the library detected nothing at all.

Fixed by invoking `case(result)`, and — more importantly — by asserting on
*why* it failed: the reported traceback must contain the injected `"boom"`
error. A negative-path test that only checks *that* something failed can
silently rot into a no-op; one that checks *how* it failed cannot.

This only surfaced because the two new edge-case tests hit the same
`run`-vs-`__call__` trap and failed loudly, which is a good argument for
adding the standards-mandated coverage rather than deferring it.

### 2. Test discovery collects imported base classes

Writing `from django_admin_tests.testcases import AdminSmokeTestCase` at
module level in the test file made both unittest and pytest collect and
run the **base class** alongside the intended subclass — discovery scans
the module namespace for `TestCase` subclasses regardless of where they
were defined. The base has no `RestrictedItem` override, so it failed on
the 403. Fixed by importing the module and referencing
`testcases.AdminSmokeTestCase` instead, keeping the bare name out of the
module namespace. Worth remembering: this same trap will apply to any host
project that imports the class directly.

### 3. pytest already understands Django tags — a design risk that evaporated

The design doc flagged "pytest users have no equivalent to
`--exclude-tag`" as a risk to solve in the `pytest-plugin` work item.
Verified during this run that pytest-django already maps
`django.test.tag()` onto pytest markers: `pytest -m django_admin_tests`
and `pytest -m "not django_admin_tests"` both filter correctly with zero
plugin code. Only a marker registration in `pyproject.toml` was needed, to
silence the unknown-mark warning. That risk can be dropped from the
`pytest-plugin` work item.

## Security Considerations

| Concern | Approach |
|---------|----------|
| Test superuser credentials | Fixed test-only literal, created inside a per-test transaction that rolls back; never a real credential — same accepted pattern as `tests/settings.py`'s `SECRET_KEY` |
| URL construction | Always via `reverse()` with names derived from model meta — never string-concatenated user input, so no injection surface |
| Permission bypass | The `RestrictedItem` fixture asserts a 403 is *expected and required*, confirming the library respects Django's permission system rather than bypassing it |

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Negative-path assertion strength | Assert on the failure's *content* (`"boom"`), not just that a failure occurred | A "did it fail?" assertion cannot distinguish real detection from an unrelated crash — as this run demonstrated firsthand |
| Base class reference in tests | Import the module, not the name | Prevents test discovery from collecting the un-overridden base class |
| Edge-case test placement | Subclasses defined inside their test functions | Keeps single-use subclasses out of module scope, so discovery doesn't pick them up as standalone test classes |

## Deviations from Plan

Two additions beyond the approved plan, both closing gaps rather than
changing direction:

1. **Two edge-case tests** (`empty registry`, `custom AdminSite`) — these
   are named as MUST-have critical-path coverage in
   `testing-standards.md`, which the original checklist had missed.
   User-confirmed before adding.
2. **`tests/custom_admin_site_urls.py`** — required to give the
   custom-`AdminSite` test real resolvable URLs, since `tests/urls.py`
   only wires the default site.

## Dependencies Added

None.

## How to Verify

1. **Run the full suite**

   ```bash
   source .venv/bin/activate
   pytest tests/
   ```

   Expected: `13 passed, 12 subtests passed`.

2. **Confirm it works under the native runner too**

   ```bash
   python manage.py test tests
   ```

   Expected: `Ran 2 tests ... OK` (only the intended subclass collected).

3. **Confirm the tag excludes it, in both runners**

   ```bash
   python manage.py test tests --exclude-tag=django_admin_tests
   pytest -m "not django_admin_tests"
   ```

   Expected: the smoke tests are deselected in both cases.

4. **Confirm the negative path genuinely detects breakage**

   ```bash
   pytest tests/test_admin_smoke.py::test_admin_smoke_testcase_detects_broken_admin_view -v
   ```

   Expected: passes — and it now asserts the failure text contains the
   injected error, so it cannot pass vacuously.

## Test Coverage

- Tests added: 13 total in suite (5 new this work item) + 12 subtests
- Coverage: 100% of `django_admin_tests/testcases.py`
- Status: passing

## Ready for Review

- [x] All acceptance criteria met
- [x] Tests passing
- [x] No critical issues
- [ ] Documentation updated (README still just a title — deferred to `packaging-release-readiness`)
- [x] Developer notes captured

## Developer Notes

- **`case(result)`, never `case.run(result)`** when driving a Django
  `TestCase` manually — `run` skips `_pre_setup`, so `self.client` and the
  test DB wrapping won't exist. This bit once already.
- Host projects importing `AdminSmokeTestCase` by name into a test module
  will have the base class collected and run alongside their subclass. If
  that turns out to bite real users, the fix is likely a
  `__test__ = False`-style guard or an abstract base split — worth
  considering during `packaging-release-readiness` when writing the README
  usage examples.
- `user_factory` is currently the only escape hatch for custom
  `AUTH_USER_MODEL`s; there's no auto-detection of required fields, and
  `testapp` uses the default `User`, so that path is untested. Flag if a
  consumer reports trouble.

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-003*
