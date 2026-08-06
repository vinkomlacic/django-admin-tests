---
id: core-package
title: Core django_admin_tests Package (v0.1)
status: in_progress
created: 2026-08-06T20:25:36Z
---

# Intent: Core django_admin_tests Package (v0.1)

## Goal

Build v0.1 of `django-admin-tests` — a pip-installable Django app giving host
projects automatic admin smoke-test coverage (changelist/add/change views
return 200) for every registered `ModelAdmin`, runnable under both
`manage.py test` and pytest, ready to tag a first release.

## Users

- Host project developers who install the package and get admin coverage for
  free with a one-line import (or zero-config under pytest).
- CI systems (host project's) that run the existing test suite, which now
  includes admin smoke coverage.

## Problem

Admin views silently break (missing fields, broken `get_queryset`, permission
misconfiguration, etc.) with no dedicated test coverage, and nobody wants to
hand-write smoke tests per registered `ModelAdmin`.

## Success Criteria

- `pip install django-admin-tests` works; `AdminSmokeTestCase` is importable
  and usable under `manage.py test` with zero non-Django dependencies.
- The optional `pytest11` plugin auto-discovers and registers the smoke tests
  under pytest with zero host-side code.
- Change-view testing: by default, attempt to auto-instantiate a minimal
  object via an in-house field-based instantiator; if instantiation fails,
  skip that admin's change-view check with a warning instead of failing the
  suite.
- Host projects can override the default instantiator per model via
  `django_admin_tests.register_factory(Model, factory_callable)`.
- Internal dev-only `testapp/` (sample models/admins) is exercised by this
  repo's own CI under both runners (native and pytest).
- GitHub Actions CI matrix passes across supported Python × Django versions
  × runner (native/pytest).
- `pyproject.toml` packaging metadata is complete and publishable to PyPI,
  including the `pytest11` entry-point declaration.

## Constraints

- `django_admin_tests/testcases.py` must never import pytest — it has to run
  unmodified under both `manage.py test` and pytest.
- No network calls; everything runs against the host project's local test DB.
- No third-party dependency (e.g. `model_bakery`) for object
  auto-instantiation — the minimal-instance builder is in-house.
- Must not assume a specific host project structure beyond having
  `django.contrib.admin` configured.

## Notes

Scope agreed as "full v0.1": core `AdminSmokeTestCase`, in-house
auto-instantiator with a `register_factory` override hook, optional pytest
plugin, dev-only `testapp` for dogfooding, CI matrix, and PyPI-ready
packaging — all in this one intent, decomposed into work items next.
