---
id: runner-compat-verification
title: Verify generated methods across every supported runner path
intent: per-model-test-methods
complexity: medium
mode: confirm
status: completed
depends_on:
  - generated-test-methods
created: 2026-08-18T20:12:19Z
run_id: run-django-admin-tests-008
completed_at: 2026-08-18T20:38:02.059Z
---

# Work Item: Verify generated methods across every supported runner path

## Description

Dynamically generated test methods are collected and addressed differently by
each entry point this package supports. This item proves — with tests, not
assumption — that all four work, and fixes whatever doesn't:

1. **pytest plugin auto-collection** (`django_admin_tests_auto = true`) — the
   plugin builds a `pytest.Module` from the installed `testcases.py` and calls
   `session.genitems()`. Generated methods should surface, but
   `tests/test_pytest_plugin.py:176-190` currently asserts the three *old*
   names appear in stdout (and, in the disabled case, don't).
2. **`manage.py test` node-ID selection** — selecting a single generated method
   by dotted path must work.
3. **`pytest -k` substring selection** — `pytest -k testapp_product` must match
   that model's three tests, which is one of the motivating goals.
4. **Parallel distribution** — pytest-xdist and Django's `--parallel`. This is
   the highest-risk item: Django's parallel runner pickles test cases to ship
   them to subprocesses, and generated methods must survive that round trip.

## Acceptance Criteria

- [ ] `tests/test_pytest_plugin.py` updated to assert generated method names; auto-collection enabled/disabled paths both still covered
- [ ] Test proving a single generated method is selectable by node ID under `manage.py test`
- [ ] Test proving `pytest -k <app>_<model>` selects exactly that model's tests
- [ ] Generated methods survive Django's `--parallel` (pickling round trip) — verified, and fixed if not
- [ ] Generated methods distribute correctly under `pytest-xdist` — verified, and fixed if not
- [ ] Test counts are correct: N registered models × 3 views, minus any documented guard test
- [ ] CI matrix extended if it doesn't already exercise the parallel paths
- [ ] Full suite passes under both `pytest` and `python -m django test --settings=tests.settings`
- [ ] `ruff check` and `ruff format --check` pass

## Technical Notes

**Parallel is the real risk.** Django's `ParallelTestSuite` uses
`multiprocessing` and pickles test-case *identities* (class + method name) to
workers, which then re-import and re-resolve them. Because generated methods
are real attributes on an importable class created at import time, each worker
regenerates the identical set — so this should hold. But it depends on
generation being deterministic and side-effect-free, and on the registry being
identical in every worker. Worth an explicit test rather than a shrug.

**Determinism matters here.** `admin.site._registry` is a dict; iteration order
follows registration order, which is stable within a process but shouldn't be
relied on across them. Method *names* are what get pickled, so ordering only
affects report ordering — but if the design doc chose any collision-
disambiguation scheme, that scheme must be order-independent.

**pytest plugin.** No change is expected to `pytest_plugin.py` itself — it
collects the module, not individual names — but confirm, since a metaclass
executing at import time inside `_collect_smoke_items`' `try/except` could now
turn a generation error into a swallowed collection warning rather than a hard
failure. Check that a genuine bug in generation doesn't get silently
downgraded to a warning.

**Existing assertions to update**: `tests/test_pytest_plugin.py:176-178`
(three `fnmatch_lines` on old names) and `:190` (negative assertion on
`test_admin_smoke_changelist_returns_200`).

## Dependencies

- generated-test-methods
