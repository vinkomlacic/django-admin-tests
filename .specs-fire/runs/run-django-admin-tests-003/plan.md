---
run: run-django-admin-tests-003
work_item: admin-smoke-testcase-core
intent: core-package
mode: validate
checkpoint: plan
approved_at: pending
---

# Implementation Plan: AdminSmokeTestCase core (changelist + add views)

Based on approved design document:
`.specs-fire/intents/core-package/work-items/admin-smoke-testcase-core-design.md`

## Implementation Checklist

- [ ] `AdminSmokeTestCase` class attrs: `admin_site`, `allowed_status_codes`, `model_allowed_status_codes`, `user_factory`
- [ ] `@tag("django_admin_tests")` on the class
- [ ] `setUpTestData` (uses `user_factory` if set, else default superuser) + `setUp` (client login)
- [ ] `_reverse_admin_url` helper (namespace via `admin_site.name`)
- [ ] `_assert_allowed_status` helper (per-model override lookup, `subTest`, named failure message)
- [ ] `test_admin_smoke_changelist_returns_200`
- [ ] `test_admin_smoke_add_view_returns_200`
- [ ] Docstrings on class + public methods/attributes
- [ ] `tests/test_admin_smoke.py`: dogfood subclass, `model_allowed_status_codes = {RestrictedItem: {403}}`
- [ ] Negative-path test with try/finally restoration
- [ ] Verify under both `pytest` and `manage.py test`, plus `--exclude-tag`

## Files to Create

| File | Purpose |
|------|---------|
| `tests/test_admin_smoke.py` | Dogfood subclass against `testapp` (positive path incl. the 403 override) + negative-path failure-detection test |

## Files to Modify

| File | Changes |
|------|---------|
| `django_admin_tests/testcases.py` | Replace the stub with the full `AdminSmokeTestCase` implementation per the design doc |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_admin_smoke.py` | `AdminSmokeTestCase` against `testapp`'s 4 models (positive + 403 override), negative-path detection of a broken admin, `--exclude-tag` behavior |

## Technical Details

Implementation order: helpers first (`_reverse_admin_url`,
`_assert_allowed_status`), then the two test methods, then the auth
plumbing (`setUpTestData`/`setUp`/`user_factory`), then the class-level
`@tag`. `tests/test_admin_smoke.py` is written last since it exercises the
finished class against real `testapp` fixtures.

The negative-path test monkeypatches `CategoryAdmin.__class__.get_queryset`
(not `django.contrib.admin.site` registration) so it needs no new URL
wiring — `admin:testapp_category_changelist` is already resolvable via
`tests/urls.py`. Restored in a `finally` block regardless of assertion
outcome.

## Based on Design Doc

Reference: `.specs-fire/intents/core-package/work-items/admin-smoke-testcase-core-design.md`

---
This is Checkpoint 2 of Validate mode.
Approve implementation plan? [Y/n/edit]
