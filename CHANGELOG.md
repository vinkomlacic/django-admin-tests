# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Tag-triggered release pipeline (`.github/workflows/release.yml`): builds
  the sdist/wheel, publishes to PyPI via Trusted Publishing, and creates a
  GitHub Release from the matching CHANGELOG section. The package version
  is now derived from git tags via `hatch-vcs` (bare, e.g. `0.1.0` — no
  `v` prefix) instead of being hand-edited in `pyproject.toml`.

### Fixed

- CI: pin `pytest-django<4.13` for the Django 4.2 test matrix cells.
  pytest-django 4.13 dropped Django 4.2 support and raises
  `AttributeError: _pre_setup_ran_eagerly` at test setup when paired with
  it.

[Unreleased]: https://github.com/vinkomlacic/django-admin-tests/commits/master
