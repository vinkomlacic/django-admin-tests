---
run: run-django-admin-tests-005
work_item: pytest-plugin
intent: core-package
generated: 2026-08-06T22:10:00Z
status: passed
---

# Test Report: Optional pytest11 auto-discovery plugin

## Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit | 51 | 0 | 0 | 100% |
| Integration | 13 | 0 | 1 | 100% |
| **Total** | 64 | 0 | 1 | 100% |

(45 carried over; 19 new this work item. The 1 skip remains the
deliberate `SelfReferentialItem` change-view skip.)

## Acceptance Criteria Validation

- ✅ **`pytest_plugin.py` registered via `pytest11` entry point** — declared in `pyproject.toml` since `package-skeleton`; `test_plugin_is_loaded_via_entry_point` asserts pytest actually loaded it, and the built wheel's `entry_points.txt` was re-inspected
- ✅ **Admin smoke tests collected and run without any import in the host project's test files** — `test_auto_collection_runs_smoke_tests_with_no_host_imports` builds a throwaway Django project in a temp dir whose only test file never mentions `django_admin_tests`, runs pytest in a subprocess, and asserts all three smoke tests appear and pass
- ✅ **Plugin only loads/executes when pytest is present** — `pytest_plugin.py` is imported solely via the entry point; `testcases.py` still contains no pytest import (existing automated test), and `manage.py test` is unaffected (verified below)
- ✅ **Running pytest against testapp collects and passes the smoke tests** — 64 passed; the `AdminSmokeTest` subclass exercises the same code path the plugin injects
- ✅ **`manage.py test` against testapp continues to pass unaffected** — `Ran 3 tests ... OK (skipped=1)`, and `--exclude-tag=django_admin_tests` still excludes cleanly

## Tests Written

### Unit Tests

- `tests/test_settings.py` (12 tests) — each accessor's default, parsed value, label normalization, and error cases (empty set, non-integer codes, malformed label, non-dict mapping)
- `tests/test_pytest_plugin.py::test_plugin_is_loaded_via_entry_point`
- `tests/test_pytest_plugin.py::test_auto_collection_ini_defaults_to_false` — guards the opt-in decision
- `tests/test_pytest_plugin.py::test_marker_is_registered`
- `tests/test_admin_smoke.py::test_allowed_status_codes_resolution_order` — class attr > settings > default, in both directions
- `tests/test_admin_smoke.py::test_excluded_models_are_not_smoke_tested` — class attr and settings exclusion

### Integration Tests

- `tests/test_pytest_plugin.py::test_auto_collection_runs_smoke_tests_with_no_host_imports` — the headline AC, end to end in a subprocess
- `tests/test_pytest_plugin.py::test_no_auto_collection_when_ini_flag_is_off` — flag off means only the host's own test runs

## Test Commands

```bash
pytest tests/
python manage.py test tests
python manage.py test tests --exclude-tag=django_admin_tests
pytest -m "not django_admin_tests"
```

## Coverage Details

| Module | Statements | Branches | Functions | Lines |
|--------|------------|----------|-----------|-------|
| `django_admin_tests/settings.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/pytest_plugin.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/testcases.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/factories.py` | 100% | 100% | 100% | 100% |
| `django_admin_tests/instantiation.py` | 100% | 100% | 100% | 100% |

## Issues Found

Three issues found and fixed before completion (none left open).

**1. Subprocess inherited this repo's Django configuration.**
The first version of the end-to-end test used `settings.configure()` in a
generated conftest and failed with `RuntimeError: Settings already
configured` — pytest-django had already configured Django from the
inherited `DJANGO_SETTINGS_MODULE`. Fixed by generating a real settings
*module*, pointing the temp project's ini at it, and clearing the
environment variable in the fixture. The rewrite also made the test
stronger: the throwaway project now defines its own app rather than
reusing `testapp`, so it proves the plugin works against an arbitrary host
project rather than our own fixtures.

**2. Throwaway settings lacked `STATIC_URL`.**
The injected smoke tests failed with `ImproperlyConfigured: You're using
the staticfiles app without having set the required STATIC_URL setting` —
the admin templates need it. A fitting failure: the smoke tests caught a
genuine admin misconfiguration in the test project, which is exactly their
purpose.

**3. The exclusion assertion was vacuous.**
`IgnoredThing` was initially a plain model that would return 200 whether or
not `ADMIN_TESTS_EXCLUDE` worked, so the exclusion wasn't actually proven.
Gave it a deliberately broken `get_queryset` that raises, so the test only
passes if the model is genuinely excluded. **Verified by experiment**:
temporarily emptying `ADMIN_TESTS_EXCLUDE` makes the test fail, confirming
it is not vacuous.

## Ready for Completion

- [x] All tests passing
- [x] Coverage target met (100%, exceeds the 90% requirement)
- [x] All acceptance criteria validated
- [x] No critical issues open

---
*Generated by specs.md - fabriqa.ai FIRE Flow Run run-django-admin-tests-005*
