---
run: run-django-admin-tests-005
work_item: pytest-plugin
intent: core-package
mode: confirm
checkpoint: plan
approved_at: pending
---

# Implementation Plan: Optional pytest11 auto-discovery plugin

## Approach

Two pieces, both driven by decisions confirmed with the user after a
feasibility probe:

**1. The plugin (`pytest_plugin.py`)** — auto-collects `AdminSmokeTestCase`
into a pytest session with no host-side import. The probe verified the
mechanism: build a `pytest.Module` collector over the installed
`testcases.py` and hand its items to the session, which lets pytest's own
`UnitTestCase` collector find the `TestCase` subclass. Injection is
**opt-in** via an ini flag (`django_admin_tests_auto = true`), default off
— installing the package must never silently add tests that fail an
existing CI. The plugin also registers the `django_admin_tests` marker, so
consumers don't get `PytestUnknownMarkWarning`.

**2. Settings-based configuration (`settings.py`)** — without this,
zero-config collection is only viable for projects where every admin
returns 200 (the probe demonstrated this concretely: the auto-collected
base class failed on `RestrictedItem`'s intentional 403). Host projects
configure via Django settings, no Python required:

| Setting | Purpose |
|---------|---------|
| `ADMIN_TESTS_ALLOWED_STATUS_CODES` | Global allowed statuses (default `{200}`) |
| `ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES` | Per-model overrides, keyed `"app_label.ModelName"` |
| `ADMIN_TESTS_EXCLUDE` | Models to skip entirely, same key format |

Class attributes on `AdminSmokeTestCase` change from concrete defaults to
`None`, with explicit resolution order: **class attribute (if set) →
Django setting → built-in default**. Settings use string model labels
since settings modules can't reasonably hold model classes.

## Files to Create

| File | Purpose |
|------|---------|
| `django_admin_tests/settings.py` | Typed accessors for the three settings, with label normalization and validation |
| `tests/test_settings.py` | Accessor unit tests: defaults, overrides, label normalization, invalid input |
| `tests/test_pytest_plugin.py` | Plugin tests incl. a `pytester` subprocess run proving zero-config collection end to end |

## Files to Modify

| File | Changes |
|------|---------|
| `django_admin_tests/pytest_plugin.py` | Replace stub: `pytest_addoption`, `pytest_configure` (marker registration), `pytest_collection_modifyitems` (opt-in injection) |
| `django_admin_tests/testcases.py` | Class attrs default to `None`; add resolution helpers consulting settings; honor exclusions |
| `tests/conftest.py` | Add `pytest_plugins = ["pytester"]` |
| `pyproject.toml` | Drop the now-redundant local marker registration (the plugin registers it) |
| `testapp`/`tests/settings.py` | Exercise the settings path for `RestrictedItem`'s 403 |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_settings.py` | Each accessor: absent setting → default, present → parsed, bad label/type → clear error |
| `tests/test_pytest_plugin.py` | Marker registered; injection no-ops when ini flag off; injects when on; `pytester` subprocess proves collection with zero host-side imports |
| `tests/test_admin_smoke.py` | Resolution order: class attr beats settings beats default; exclusions honored |

## Technical Details

Guard the injection hook so a missing/unconfigured Django (or an import
error in the host's admin) degrades gracefully rather than crashing
collection of unrelated tests.

`manage.py test` must stay unaffected — verified by re-running the native
runner, since `pytest_plugin.py` is never imported on that path.

The `pytester` integration test is the one that actually proves the
headline AC ("collected without any import in the host project's own test
files"); the unit tests around it are supporting evidence, not a
substitute.

---
This is Checkpoint 1 of Confirm mode.
Approve plan? [Y/n/edit]
