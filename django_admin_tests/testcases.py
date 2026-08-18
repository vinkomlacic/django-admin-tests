"""AdminSmokeTestCase: asserts every registered ModelAdmin's changelist/add/
change views return 200 (or another allowed status).

One test method is generated per (registered model, view) pair at class
creation time, named ``test_admin_smoke_<app_label>_<model_name>_<view>``, so
a broken admin fails under its own name and can be re-run on its own.

This module must never import pytest — it has to run unmodified under both
``manage.py test`` and pytest (see coding-standards.md).
"""

import warnings

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, tag
from django.urls import NoReverseMatch, reverse

from django_admin_tests.factories import get_factory
from django_admin_tests.instantiation import (
    AdminSmokeWarning,
    InstanceBuildError,
    build_instance,
)
from django_admin_tests.settings import (
    DEFAULT_ALLOWED_STATUS_CODES,
    get_allowed_status_codes,
    get_excluded_admins,
    get_model_allowed_status_codes,
    model_label,
)

__all__ = ["AdminSmokeTestCase", "DEFAULT_ALLOWED_STATUS_CODES"]

#: Admin views smoke-tested for every registered model.
VIEW_NAMES = ("changelist", "add", "change")

#: Method generated when an ``AdminSite`` has no registered admins at all.
EMPTY_REGISTRY_METHOD_NAME = "test_admin_smoke_no_registered_admins"


def _generated_method_name(model, view_name):
    """Return the test method name generated for ``model``'s ``view_name`` view."""
    opts = model._meta
    return f"test_admin_smoke_{opts.app_label}_{opts.model_name}_{view_name}"


def _describe(test, model, view_name):
    """Name a generated test after its model/view so reports read correctly."""
    test.__name__ = _generated_method_name(model, view_name)
    test.__doc__ = (
        f"{model._meta.label} {view_name} view returns an allowed status code."
    )
    return test


def _make_view_test(model, view_name):
    """Build the test method for a changelist or add view."""

    def test(self):
        self._skip_if_excluded(model)
        url = self._reverse_admin_url(model, view_name)
        response = self._get_admin_view(model, view_name, url)
        self._assert_allowed_status(model, view_name, response)

    return _describe(test, model, view_name)


def _make_change_view_test(model):
    """Build the test method for a change view.

    Unlike the other views, this one needs an object to point at, so it
    carries the skip-with-warning path for models no instance can be
    produced for.
    """

    def test(self):
        self._skip_if_excluded(model)
        instance = self._get_change_view_instance(model)
        if instance is None:
            message = (
                f"Skipping {model.__name__} change view: could not build "
                f"an instance. Register a factory with "
                f"django_admin_tests.register_factory({model.__name__}, ...) "
                f"to cover it."
            )
            warnings.warn(message, AdminSmokeWarning, stacklevel=2)
            self.skipTest(message)
        url = self._reverse_admin_url(model, "change", args=[instance.pk])
        response = self._get_admin_view(model, "change", url)
        self._assert_allowed_status(model, "change", response)

    return _describe(test, model, "change")


def _make_empty_registry_test():
    """Build the placeholder used when an ``AdminSite`` registers nothing.

    Without it a site with no admins would generate no methods at all, which
    is indistinguishable from the smoke tests never having run.
    """

    def test(self):
        """No ModelAdmins are registered; there is nothing to smoke-test."""

    test.__name__ = EMPTY_REGISTRY_METHOD_NAME
    return test


def _build_generated_tests(admin_site):
    """Map method name to test function for everything registered on ``admin_site``."""
    generated = {}
    claimed_by = {}

    for model in admin_site._registry:
        for view_name in VIEW_NAMES:
            method_name = _generated_method_name(model, view_name)
            claimant = claimed_by.get(method_name)
            if claimant is not None:
                raise ImproperlyConfigured(
                    f"django-admin-tests cannot generate a unique test name for "
                    f"{model._meta.label} and {claimant._meta.label}: both map to "
                    f"{method_name!r}. Their app labels and model names differ only "
                    f"in where the underscore falls. Exclude one of them via "
                    f"ADMIN_TESTS_EXCLUDE to smoke-test the other."
                )
            claimed_by[method_name] = model
            if view_name == "change":
                generated[method_name] = _make_change_view_test(model)
            else:
                generated[method_name] = _make_view_test(model, view_name)

    if not generated:
        placeholder = _make_empty_registry_test()
        generated[placeholder.__name__] = placeholder

    return generated


class AdminSmokeMeta(type):
    """Binds one test method per (registered model, view) onto the class.

    Generation has to happen here rather than in ``__init_subclass__``: that
    hook doesn't fire for the class defining it, which would leave the base
    ``AdminSmokeTestCase`` — the class the pytest plugin collects directly —
    carrying no tests at all.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        admin_site = getattr(cls, "admin_site", None)
        if admin_site is None:
            return cls

        generated = _build_generated_tests(admin_site)

        # Read off the freshly built class, so this is whatever the bases
        # generated — precisely the set that may no longer apply here.
        inherited = getattr(cls, "_admin_smoke_generated", frozenset())
        for stale in inherited - generated.keys():
            # Not delattr: the attribute lives on the base, not on cls. Both
            # unittest's getTestCaseNames and pytest's unittest collector keep
            # only names where getattr(...) is callable, so None removes the
            # method from collection under either runner. Restricted to names
            # we generated, so a host project's own tests are never touched.
            setattr(cls, stale, None)

        for method_name, method in generated.items():
            if method_name in namespace:
                # The class defines this one itself — an explicit override of a
                # single model's check. Overwriting it would silently discard
                # what the author wrote.
                continue
            method.__qualname__ = f"{cls.__qualname__}.{method_name}"
            setattr(cls, method_name, method)

        # Overridden names are deliberately left out: this set is what future
        # subclasses are allowed to neutralize, and a hand-written method is
        # never ours to remove.
        cls._admin_smoke_generated = frozenset(generated.keys() - namespace.keys())
        return cls


@tag("django_admin_tests")
class AdminSmokeTestCase(TestCase, metaclass=AdminSmokeMeta):
    """Smoke-tests every ModelAdmin registered on ``admin_site``.

    One test method is generated per (registered model, view) pair, named
    ``test_admin_smoke_<app_label>_<model_name>_<view>`` — for example
    ``test_admin_smoke_auth_user_changelist``. Each asserts its view returns
    a status code in ``allowed_status_codes`` (or the per-model override in
    ``model_allowed_status_codes``).

    Because the methods are generated when the class is created, the admin
    registry is read at import time. Admins registered later than that won't
    be covered; in practice registration happens during app loading, which
    always precedes test module import.

    Change views need an object to point at. One is resolved per model in
    this order: a factory registered via
    ``django_admin_tests.register_factory``, then any existing row, then a
    minimal instance built automatically from the model's fields. If none
    of those work, that model's change-view check is skipped with an
    ``AdminSmokeWarning`` rather than failing the suite.

    Host projects can customize by subclassing:

    - ``admin_site``: test a custom ``AdminSite`` instead of the default.
      Methods generated for the parent's registry that don't apply to the
      new site are dropped automatically.
    - ``allowed_status_codes``: the globally allowed status set.
    - ``model_allowed_status_codes``: per-model overrides, e.g. for admins
      that intentionally deny access (``{MyModel: {403}}``).
    - ``excluded_models``: models to skip entirely. Excluded models are
      resolved per test run, so their methods still exist and report as
      skipped.
    - ``user_factory``: a zero-argument callable returning the user used to
      authenticate requests, for projects with a non-default
      ``AUTH_USER_MODEL``. Defaults to creating a disposable superuser.

    All of the above except ``admin_site`` and ``user_factory`` can also be
    set in Django settings (``ADMIN_TESTS_ALLOWED_STATUS_CODES``,
    ``ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES``, ``ADMIN_TESTS_EXCLUDE``),
    which is how projects configure the pytest plugin's auto-collected
    tests without writing any Python. Resolution order is: class attribute
    if set, then the Django setting, then the built-in default — so the
    class attributes default to ``None`` rather than to a concrete value.

    Exclude this test entirely with ``--exclude-tag=django_admin_tests``
    (Django runner) or ``-m "not django_admin_tests"`` (pytest).
    """

    admin_site = admin.site
    allowed_status_codes = None
    model_allowed_status_codes = None
    excluded_models = None
    user_factory = None

    @classmethod
    def setUpTestData(cls):
        if cls.user_factory is not None:
            cls.admin_smoke_test_user = cls.user_factory()
        else:
            cls.admin_smoke_test_user = cls._create_default_superuser()

    @classmethod
    def _create_default_superuser(cls):
        """Create a disposable superuser for the default AUTH_USER_MODEL.

        Projects with a custom user model needing different required
        fields should set ``user_factory`` instead of relying on this.
        """
        user_model = get_user_model()
        return user_model.objects.create_superuser(
            username="admin-smoke-test",
            email="admin-smoke-test@example.com",
            password="admin-smoke-test-password",
        )

    def setUp(self):
        self.client.force_login(self.admin_smoke_test_user)

    def _reverse_admin_url(self, model, view_name, args=None):
        opts = model._meta
        url_name = (
            f"{self.admin_site.name}:{opts.app_label}_{opts.model_name}_{view_name}"
        )
        try:
            return reverse(url_name, args=args)
        except NoReverseMatch as exc:
            self.fail(f"Could not resolve {view_name} URL for {model.__name__}: {exc}")

    def _get_admin_view(self, model, view_name, url):
        """GET ``url``, turning a form-field ``KeyError`` into a clear failure.

        A field named in ``ModelAdmin.fields``/``fieldsets`` but absent from
        the actual rendered ``ModelForm`` — commonly because it's excluded,
        non-editable, or a value the model's own ``save()`` populates and
        the ``ModelAdmin`` forgot to also list in ``readonly_fields`` — isn't
        caught by Django's system checks. It only surfaces as a bare
        ``KeyError`` when the admin form is rendered, which would otherwise
        show up as an opaque traceback instead of naming the model.
        """
        try:
            return self.client.get(url)
        except KeyError as exc:
            self.fail(
                f"{model.__name__} {view_name} view raised {exc!r} while "
                f"rendering the admin form. This is commonly caused by a "
                f"field listed in `fields`/`fieldsets` that isn't in the "
                f"ModelForm (e.g. excluded, non-editable, or missing from "
                f"`readonly_fields`) — check {model.__name__}'s ModelAdmin."
            )

    def _get_change_view_instance(self, model):
        """Resolve an instance to exercise ``model``'s change view.

        Order: registered factory, then an existing row, then an
        auto-built minimal instance. Returns None if none succeed, leaving
        the caller to skip the check.
        """
        factory = get_factory(model)
        if factory is not None:
            instance = factory()
            if instance.pk is None:
                instance.save()
            return instance

        existing = model._default_manager.first()
        if existing is not None:
            return existing

        try:
            return build_instance(model)
        except InstanceBuildError:
            return None

    def _is_excluded(self, model):
        """Whether ``model`` is opted out by class attribute or Django settings.

        Checked per test run rather than when the methods are generated, so
        ``override_settings(ADMIN_TESTS_EXCLUDE=...)`` still takes effect.
        """
        excluded_models = self.excluded_models or ()
        if model in excluded_models:
            return True
        return model_label(model) in get_excluded_admins()

    def _skip_if_excluded(self, model):
        if self._is_excluded(model):
            self.skipTest(f"{model._meta.label} is excluded from the admin smoke tests")

    def _allowed_status_codes_for(self, model):
        """Resolve allowed statuses: class attribute, then settings, then default."""
        class_overrides = self.model_allowed_status_codes or {}
        if model in class_overrides:
            return class_overrides[model]

        settings_overrides = get_model_allowed_status_codes()
        label = model_label(model)
        if label in settings_overrides:
            return settings_overrides[label]

        if self.allowed_status_codes is not None:
            return self.allowed_status_codes
        return get_allowed_status_codes()

    def _assert_allowed_status(self, model, view_name, response):
        allowed = self._allowed_status_codes_for(model)
        self.assertIn(
            response.status_code,
            allowed,
            msg=(
                f"{model.__name__} {view_name} view returned "
                f"{response.status_code}, expected one of {sorted(allowed)}"
            ),
        )
