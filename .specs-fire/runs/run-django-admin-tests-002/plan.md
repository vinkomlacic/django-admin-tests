---
run: run-django-admin-tests-002
work_item: dev-testapp
intent: core-package
mode: confirm
checkpoint: plan
approved_at: pending
---

# Implementation Plan: Dev-only testapp for dogfooding

## Approach

Create the `testapp/` Django app (models + admin registrations only, per
`coding-standards.md`'s file layout) and wire it into a minimal Django
project whose **settings module lives at `tests/settings.py`**, per the
existing command in `testing-standards.md`:
`python -m django test --settings=tests.settings`. So `testapp/` supplies
the app-under-test; `tests/` supplies the project config (settings, urls)
*and* this repo's own pytest suite that exercises it — matching the
convention already established in that doc.

Four sample models cover the four required scenarios:

| Model | Scenario |
|-------|----------|
| `Category` | Plain model, no relations |
| `Product` | FK relation (→ `Category`) |
| `EmptyOnlyModel` | Deliberately zero rows — empty-table scenario for change-view instantiation later |
| `RestrictedItem` | Admin overrides `has_module_permission`/`has_view_permission` to always deny — exercises configurable allowed-status handling |

A root `manage.py` (pointing at `DJANGO_SETTINGS_MODULE=tests.settings`)
is added so `manage.py check`/`manage.py test` work per the acceptance
criteria and `system-architecture.md`'s dual-runner requirement.
`pyproject.toml` gets a `[tool.pytest.ini_options]` block pointing
pytest-django at `tests.settings`.

Wheel packaging already scopes to `django_admin_tests` only
(`[tool.hatch.build.targets.wheel] packages`), so `testapp/` and `tests/`
are excluded from the build with no additional config — verified again in
this run rather than assumed.

## Files to Create

| File | Purpose |
|------|---------|
| `testapp/__init__.py` | App package marker |
| `testapp/models.py` | 4 sample models covering the required scenarios |
| `testapp/admin.py` | `ModelAdmin` registrations for all 4 models, including the permission-denying `RestrictedItemAdmin` |
| `testapp/migrations/__init__.py` | Migrations package marker |
| `testapp/migrations/0001_initial.py` | Generated via `manage.py makemigrations` |
| `tests/settings.py` | Minimal Django settings: sqlite in-memory DB, `INSTALLED_APPS` (incl. `django_admin_tests`, `testapp`), middleware/templates needed for the admin to render, `ROOT_URLCONF = "tests.urls"` |
| `tests/urls.py` | `urlpatterns = [path("admin/", admin.site.urls)]` |
| `manage.py` (repo root) | Standard Django management entrypoint, `DJANGO_SETTINGS_MODULE=tests.settings` |
| `tests/test_testapp.py` | Verifies testapp is correctly wired: all 4 models registered, `EmptyOnlyModel` truly empty, `RestrictedItem` admin truly denies access, and a real admin changelist request round-trips (200 for `Category`, 403 for `RestrictedItem`) — proving the whole admin URL/template/session/csrf pipeline works before later work items build on it |

## Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Add `[tool.pytest.ini_options]` with `DJANGO_SETTINGS_MODULE = "tests.settings"` |

## Tests

| Test File | Coverage |
|-----------|----------|
| `tests/test_testapp.py` | Admin registry contents, empty-table invariant, permission-denial behavior, end-to-end admin request round-trip |

## Technical Details

- `RestrictedItemAdmin` overrides permission hooks unconditionally (no
  `super()` call), so it denies access even to superusers — a genuine
  negative-path fixture rather than a role-based one, since we don't want
  test-run identity to matter here.
- `EmptyOnlyModel` gets no fixtures/factories anywhere — its zero-row state
  is the point, not an oversight.
- `SECRET_KEY` in `tests/settings.py` is a test-only placeholder value
  (`django-insecure-...`), never used outside this repo's own CI — not a
  real secret per `constitution.md`.
- `manage.py check` and `pytest tests/` both get run as verification
  before this work item is marked complete.

---
This is Checkpoint 1 of Confirm mode.
Approve plan? [Y/n/edit]
