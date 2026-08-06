---
id: dev-testapp
title: Dev-only testapp for dogfooding
intent: core-package
complexity: medium
mode: confirm
status: pending
depends_on: [package-skeleton]
created: 2026-08-06T20:27:17Z
---

# Work Item: Dev-only testapp for dogfooding

## Description

Create the dev-only `testapp/` Django project used by this repo's own test
suite to dogfood `AdminSmokeTestCase`. Include a minimal settings module and
sample models registered in admin.py covering distinct scenarios: a plain
model, a model with an FK relation, a model with zero rows in the test DB
(to exercise change-view instantiation later), and a model admin with
restricted permissions (to verify allowed-status configurability).

## Acceptance Criteria

- [ ] `testapp/` is a valid minimal Django project (settings module) not shipped in the package distribution
- [ ] At least 4 sample models covering: plain model, FK relation, empty-table scenario, permission-restricted admin
- [ ] Each sample model registered via `@admin.register` or `admin.site.register` with a `ModelAdmin`
- [ ] testapp is excluded from the package build (not included in sdist/wheel)
- [ ] `manage.py check` passes against testapp settings

## Technical Notes

This app only exists for this repo's own CI (system-architecture.md,
"Internal testapp" component). Keep models simple — the goal is
admin-registry coverage, not realistic domain modeling.

## Dependencies

- package-skeleton
