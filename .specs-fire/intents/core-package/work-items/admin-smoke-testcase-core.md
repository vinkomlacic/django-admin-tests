---
id: admin-smoke-testcase-core
title: AdminSmokeTestCase core (changelist + add views)
intent: core-package
complexity: high
mode: validate
status: pending
depends_on: [package-skeleton, dev-testapp]
created: 2026-08-06T20:27:17Z
---

# Work Item: AdminSmokeTestCase core (changelist + add views)

## Description

Implement `AdminSmokeTestCase` in `django_admin_tests/testcases.py`: a Django
`TestCase` subclass that iterates every registered `ModelAdmin` in
`admin.site._registry`, resolves each admin's changelist and add view URLs,
issues requests via the Django test client, and asserts a 200 (or another
configurable allowed status) response. Change-view testing is explicitly out
of scope for this item (see change-view-instantiation). Must run correctly
under `manage.py test` using testapp for verification, without importing
pytest.

## Acceptance Criteria

- [ ] AdminSmokeTestCase discovers every entry in `admin.site._registry` at test run time (no hardcoded model list)
- [ ] For each registered ModelAdmin, changelist view URL is resolved and requested; response status asserted against allowed statuses (default {200})
- [ ] For each registered ModelAdmin, add view URL is resolved and requested; response status asserted against allowed statuses
- [ ] Allowed status set is configurable (e.g. per-class attribute or settings) to accommodate custom permission-denied flows
- [ ] `testcases.py` contains no pytest import anywhere
- [ ] Running `manage.py test` against testapp exercises AdminSmokeTestCase and passes
- [ ] A deliberately broken admin view in testapp causes the smoke test to fail (negative-path verification)

## Technical Notes

Use `django.test.Client` via Django's `TestCase`. Resolve URLs via the admin
site's `get_urls()`/`reverse` rather than hardcoding URL patterns, so it
survives custom `AdminSite` instances. This is the architectural core — mode
is validate, so a design doc should be reviewed before implementation.

## Dependencies

- package-skeleton
- dev-testapp
