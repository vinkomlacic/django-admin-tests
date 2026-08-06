---
run: run-django-admin-tests-005
work_item: pytest-plugin
intent: core-package
generated: 2026-08-06T22:25:00Z
mode: confirm
---

# Implementation Walkthrough: Optional pytest11 auto-discovery plugin

## Summary

The `pytest11` plugin now auto-collects the admin smoke tests into a host
project's pytest run with no import in their test files — proven end to
end by a subprocess test against a throwaway Django project. Collection is
**opt-in** via `django_admin_tests_auto = true`, and the tests it injects
are configured through Django settings, since there's no host-side Python
to subclass.

## Structure Overview

`pytest_plugin.py` implements three hooks: `pytest_addoption` (the ini
flag), `pytest_configure` (registers the `django_admin_tests` marker so
consumers don't hit `PytestUnknownMarkWarning`), and
`pytest_collection_modifyitems` (the injection). Injection works by
building a `pytest.Module` over the *installed* `testcases.py` and letting
pytest's own unittest collector find `AdminSmokeTestCase` inside it — no
synthetic test construction needed.

`settings.py` is the other half. Auto-collected tests can't be subclassed,
so `ADMIN_TESTS_ALLOWED_STATUS_CODES`, `ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES`
and `ADMIN_TESTS_EXCLUDE` provide the same control from settings.
`AdminSmokeTestCase` resolves each option as **class attribute → Django
setting → built-in default**, which is why its class attributes now default
to `None` instead of concrete values.

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `django_admin_tests/settings.py` | Settings accessors with label normalization and validation |
| `tests/test_settings.py` | 12 accessor tests, including every error path |
| `tests/test_pytest_plugin.py` | Plugin tests + the end-to-end `pytester` subprocess run |

### Modified

| File | Changes |
|------|---------|
| `django_admin_tests/pytest_plugin.py` | Stub → three hooks, opt-in injection, graceful degradation |
| `django_admin_tests/testcases.py` | `None` defaults, settings-aware resolution, exclusion support |
| `pyproject.toml` | Dropped the now-redundant marker declaration; documented why auto-collection stays off in this repo |
| `tests/conftest.py` | Enabled the `pytester` plugin |
| `tests/test_admin_smoke.py` | Resolution-order and exclusion tests |

## Key Implementation Details

### 1. A feasibility probe changed the design before any code was written

Rather than assume an injection mechanism, I probed it first: a throwaway
plugin that built a `pytest.Module` over `testcases.py` and extended the
item list. It worked — and immediately surfaced the real design problem.
The injected tests *failed* on `RestrictedItem`'s intentional 403, because
the auto-collected base class has no per-model overrides. That single
observation drove both decisions taken to the user: make collection opt-in,
and add settings-based configuration, without which zero-config only works
for projects where every admin returns 200.

### 2. Nodeid-prefix matching was the wrong dedup check

The "already collected" guard compared `item.nodeid.startswith("testcases.py")`.
Any host project with its own top-level `testcases.py` — an entirely
plausible filename — would match and silently suppress injection. Replaced
with a resolved-`Path` comparison.

### 3. The guard test asserted a guarantee the code can't make

The first version of the graceful-degradation test gave the host project a
broken `admin.py` and expected the plugin to shrug it off. Running it
showed why that's impossible: a broken admin raises inside `django.setup()`
during pytest-django's configure step, long before our hook runs. Rather
than weaken the assertion and keep a misleading name, the test was replaced
with one that targets what the guard actually protects — a failure inside
our own collection step — and its docstring now states the limitation
explicitly.

### 4. Verifying the end-to-end test isn't vacuous

`ADMIN_TESTS_EXCLUDE` pointed at a plain model that would have returned 200
whether or not exclusion worked — so the assertion proved nothing. Gave
that model a deliberately broken `get_queryset`, then **verified by
experiment** that emptying the setting makes the test fail. This is the
lesson from run-003's vacuously-passing negative test, applied
preemptively.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auto-collection default | Opt-in (`django_admin_tests_auto`, default false) | Installing a package must never silently add tests that fail an existing CI; confirmed with the user during planning |
| Configuration surface | Django settings with `"app_label.ModelName"` string keys | Settings modules can't reasonably hold model classes, and auto-collected tests can't be subclassed |
| Class-attribute defaults | `None`, resolving class → settings → built-in default | Makes "was this explicitly set?" unambiguous without sentinel-identity tricks |
| Marker registration | In the plugin, not `pyproject.toml` | Consumers get the marker registered automatically; our own config no longer needs to declare it |

## Deviations from Plan

The plan listed modifying `tests/settings.py` to exercise the settings path
for `RestrictedItem`. Not done, and deliberately: putting
`ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES` in this repo's global settings
would apply it to every test, masking whether the class-attribute path
still worked. `override_settings` in the resolution-order test covers it
more precisely, and the end-to-end subprocess test exercises the real
settings path in a real project.

## Dependencies Added

None. `pytester` ships with pytest, already a dev dependency.

## How to Verify

1. **Full suite**

   ```bash
   source .venv/bin/activate
   pytest tests/
   ```

   Expected: `65 passed, 1 skipped`.

2. **The headline claim, end to end**

   ```bash
   pytest tests/test_pytest_plugin.py::test_auto_collection_runs_smoke_tests_with_no_host_imports -v
   ```

   Expected: passes — a temp Django project whose only test file never
   mentions `django_admin_tests` still runs all three smoke tests.

3. **Native runner unaffected**

   ```bash
   python manage.py test tests
   ```

   Expected: `Ran 3 tests ... OK (skipped=1)`.

## Test Coverage

- Tests added: 65 total in suite (20 new this work item) + 20 subtests
- Coverage: 100% across all five shipped modules
- Status: passing

## Ready for Review

- [x] All acceptance criteria met
- [x] Tests passing
- [x] No critical issues
- [ ] Documentation updated (README still a stub — `packaging-release-readiness` owns this, and now has more to cover)
- [x] Developer notes captured

## Developer Notes

- Auto-collection stays **off** for this repo, on purpose: our `testapp`
  registers a permission-denying admin that the un-subclassed base class
  would correctly fail on. `pyproject.toml` says so inline, and a test
  asserts the flag is false so anyone flipping it learns why it broke.
- The README needs to be honest that the quickstart is install + one ini
  line, not truly zero-config, and document the three `ADMIN_TESTS_*`
  settings. Noted in the review report for the next work item.
- If a host project's admin raises on import, `django.setup()` fails and
  their whole session dies before this plugin runs. That's Django's error
  to report; the plugin's guard covers only failures inside its own
  collection step.

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-005*
