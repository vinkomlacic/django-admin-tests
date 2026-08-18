# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Breaking**: `AdminSmokeTestCase` now generates one test method per
  (registered model, view) instead of three methods that looped over the
  admin registry with `subTest`. Methods are named
  `test_admin_smoke_<app_label>_<model_name>_<view>`, e.g.
  `test_admin_smoke_shop_product_changelist`. A broken admin now fails
  under its own name, individual models can be re-run with
  `pytest -k shop_product`, and the per-model tests distribute across
  parallel workers.

  The three previous method names —
  `test_admin_smoke_changelist_returns_200`,
  `test_admin_smoke_add_view_returns_200` and
  `test_admin_smoke_change_view_returns_200` — no longer exist. If you
  select them by node ID anywhere (CI config, `--exclude-tag` is
  unaffected), update those references. Reported test counts will rise
  from 3 to roughly 3 × the number of registered admins.
- Models opted out via `excluded_models` or `ADMIN_TESTS_EXCLUDE` now
  report as skipped rather than silently not existing. Exclusions are
  resolved per run, so `override_settings(ADMIN_TESTS_EXCLUDE=...)` still
  takes effect.
- A subclass that sets its own `admin_site` no longer inherits the parent's
  generated methods. A test method the subclass defines itself always wins
  over the generated one of the same name.

### Added

- `ImproperlyConfigured` is raised if two registered models would generate
  the same test method name (possible when app labels and model names
  differ only in where the underscore falls), rather than silently dropping
  one model's coverage.

## [0.1.1] - 2026-08-08

### Fixed

- `AdminSmokeTestCase`: a `ModelAdmin` field referenced in `fields`/
  `fieldsets` but missing from the rendered `ModelForm` (e.g. excluded,
  non-editable, or a `save()`-populated field left out of
  `readonly_fields`) now fails with a clear message naming the model,
  instead of a bare `KeyError` (#1).

### Changed

- Docs site: added a "Better than nothing" line to the tagline.

## [0.1.0] - 2026-08-08

### Added

- `AdminSmokeTestCase`: asserts the changelist, add and change views of
  every registered `ModelAdmin` return an allowed status (default `200`).
  Runs under both `manage.py test` and pytest; imports no pytest itself.
- Configurable per test case via `admin_site`, `allowed_status_codes`,
  `model_allowed_status_codes`, `excluded_models` and `user_factory`.
- Configurable via Django settings for projects using the pytest plugin:
  `ADMIN_TESTS_ALLOWED_STATUS_CODES`,
  `ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES`, `ADMIN_TESTS_EXCLUDE`.
  Resolution order is class attribute → setting → built-in default.
- Dependency-free minimal-instance builder so change views can be tested
  without fixtures. Models it can't construct are skipped with an
  `AdminSmokeWarning` rather than failing the suite.
- `register_factory(Model, callable)` to supply instances for models the
  builder can't handle.
- Optional `pytest11` plugin for collecting the smoke tests with no import
  in the host project's test files. Opt-in via
  `django_admin_tests_auto = true`.
- All tests tagged `django_admin_tests`, so they can be excluded with
  `--exclude-tag=django_admin_tests` or `-m "not django_admin_tests"`.

[Unreleased]: https://github.com/vinkomlacic/django-admin-tests/commits/master
