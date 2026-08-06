# django-admin-tests

[![CI](https://github.com/vinkomlacic/django-admin-tests/actions/workflows/ci.yml/badge.svg)](https://github.com/vinkomlacic/django-admin-tests/actions/workflows/ci.yml)

Automatic admin smoke-test coverage for Django projects.

Every `ModelAdmin` you register gets its changelist, add and change views
asserted to return `200` — as part of *your* test run, under either
`manage.py test` or pytest. Admin pages break quietly: a renamed field in
`list_display`, a `get_queryset` that blows up on a related lookup, a
permission tweak. This catches that without you writing a test per model.

## Install

```bash
pip install django-admin-tests
```

Requires Python 3.10+ and Django 4.2+.

## Usage

There are two ways in. Both run under either test runner.

### Option 1 — subclass it (works everywhere)

Put this in any test module your runner already collects:

```python
from django_admin_tests.testcases import AdminSmokeTestCase


class AdminSmokeTest(AdminSmokeTestCase):
    pass
```

That's it. Subclassing is also how you customize behavior:

```python
from django_admin_tests.testcases import AdminSmokeTestCase

from myapp.models import InternalReport, LegacyThing


class AdminSmokeTest(AdminSmokeTestCase):
    # Admins that intentionally deny access:
    model_allowed_status_codes = {InternalReport: {403}}
    # Admins to skip entirely:
    excluded_models = {LegacyThing}
```

> **Note:** import the *module*, not the class, if you'd rather the base
> class not be collected as a test in its own right. Test discovery scans
> the whole module namespace for `TestCase` subclasses, so
> `from django_admin_tests.testcases import AdminSmokeTestCase` makes the
> un-customized base class run too. `from django_admin_tests import
> testcases` and then `testcases.AdminSmokeTestCase` avoids that.

### Option 2 — pytest plugin (no test file needed)

If you use pytest, the bundled plugin can collect the smoke tests without
you writing anything. It's **opt-in** — installing this package will never
silently add tests to your suite:

```toml
# pyproject.toml
[tool.pytest.ini_options]
django_admin_tests_auto = true
```

Since there's no class to subclass in this mode, configure it through
Django settings instead (see below).

## Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `ADMIN_TESTS_ALLOWED_STATUS_CODES` | `{200}` | Globally accepted response statuses |
| `ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES` | `{}` | Per-model overrides, keyed `"app_label.ModelName"` |
| `ADMIN_TESTS_EXCLUDE` | `[]` | Models to skip entirely, same key format |

```python
# settings.py
ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES = {"myapp.InternalReport": [403]}
ADMIN_TESTS_EXCLUDE = ["myapp.LegacyThing"]
```

Resolution order is **class attribute → Django setting → built-in
default**, so a subclass always wins over settings.

## Change views need an object

To load a change view, there has to be something to change. An instance is
resolved per model in this order:

1. A factory you registered for that model
2. Any existing row
3. A minimal instance built automatically from the model's fields

If none of those work — most often a required self-referential or circular
foreign key — that model's change-view check is **skipped with a warning**,
not failed. Register a factory to cover it:

```python
# In your AppConfig.ready(), conftest.py, or anywhere that runs at startup
from django_admin_tests import register_factory

from myapp.models import Tricky


def make_tricky():
    return Tricky.objects.create(...)


register_factory(Tricky, make_tricky)
```

The auto-builder is in-house and dependency-free — installing this package
pulls in nothing but Django.

## Turning it off

The tests are tagged `django_admin_tests`:

```bash
python manage.py test --exclude-tag=django_admin_tests
pytest -m "not django_admin_tests"
```

## Custom user models

The test client authenticates as a superuser it creates itself, using the
default `User` fields. If your `AUTH_USER_MODEL` needs something else,
supply a factory:

```python
class AdminSmokeTest(AdminSmokeTestCase):
    user_factory = staticmethod(my_superuser_factory)
```

## Custom admin sites

```python
from myproject.admin import my_site


class AdminSmokeTest(AdminSmokeTestCase):
    admin_site = my_site
```

## Known limitations

- Models whose change view can't be instantiated are skipped with a
  warning rather than failed. That's deliberate — a smoke test shouldn't
  fail because a model is awkward to construct — but it does mean an
  un-covered model can go unnoticed. The warning names it.
- The auto-builder doesn't try to satisfy custom `save()`/`clean()`
  requirements. Use `register_factory` for those.
- Custom `AUTH_USER_MODEL` support is the `user_factory` hook only; there's
  no auto-detection of required fields.
- Many-to-many fields aren't populated (they aren't needed for the views to
  render).

## License

MIT — see [LICENSE](LICENSE).
