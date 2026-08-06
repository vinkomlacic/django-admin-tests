---
id: change-view-instantiation
title: In-house auto-instantiator for change-view testing
intent: core-package
complexity: high
mode: validate
status: pending
depends_on: [admin-smoke-testcase-core]
created: 2026-08-06T20:27:17Z
---

# Work Item: In-house auto-instantiator for change-view testing

## Description

Extend AdminSmokeTestCase's coverage to change views. Implement an in-house,
dependency-free minimal-instance auto-instantiator that inspects a model's
fields and constructs+saves a minimal valid instance (naive per-field-type
defaults for required fields). Wire it into the change-view assertion:
attempt auto-instantiation (or a registered factory, if present) before
requesting the change view; if instantiation fails, skip that admin's
change-view check and emit a warning rather than failing the test. Provide
`django_admin_tests.register_factory(Model, factory_callable)` so host
projects can override the default instantiator per model.

## Acceptance Criteria

- [ ] In-house instantiator fills required fields with type-appropriate naive defaults (CharField/TextField -> short string, IntegerField -> 0, ForeignKey -> auto-instantiate or reuse related object, DateField/DateTimeField -> now, BooleanField -> False, etc.)
- [ ] No third-party dependency introduced for instantiation (no model_bakery or similar)
- [ ] `register_factory(Model, callable)` registry exists; registered factories take precedence over the default instantiator for that model
- [ ] Change view is requested against the instantiated/factory-provided object; response status asserted against allowed statuses
- [ ] If both the registered factory (if any) and the default instantiator fail to produce a saved instance, the change-view check for that admin is skipped (not failed) and a warning is emitted identifying the model
- [ ] testapp's empty-table / complex-FK sample models exercise both the auto-instantiate success path and the skip+warning path
- [ ] No pytest import in testcases.py

## Technical Notes

Architectural decision area — needs a short design doc (validate mode)
covering: field-type -> default value mapping, FK cycle handling
(self-referential or circular FKs), and where `register_factory` state lives
(module-level registry vs. app config).

## Dependencies

- admin-smoke-testcase-core
