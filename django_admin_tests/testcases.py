"""AdminSmokeTestCase: asserts every registered ModelAdmin's changelist/add/
change views return 200 (or another allowed status).

This module must never import pytest — it has to run unmodified under both
``manage.py test`` and pytest (see coding-standards.md).
"""

import warnings

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import NoReverseMatch, reverse

from django_admin_tests.factories import get_factory
from django_admin_tests.instantiation import (
    AdminSmokeWarning,
    InstanceBuildError,
    build_instance,
)

DEFAULT_ALLOWED_STATUS_CODES = {200}


@tag("django_admin_tests")
class AdminSmokeTestCase(TestCase):
    """Smoke-tests every ModelAdmin registered on ``admin_site``.

    Iterates ``admin_site._registry`` and asserts that the changelist, add
    and change views for each registered ``ModelAdmin`` return a status
    code in ``allowed_status_codes`` (or the per-model override in
    ``model_allowed_status_codes``).

    Change views need an object to point at. One is resolved per model in
    this order: a factory registered via
    ``django_admin_tests.register_factory``, then any existing row, then a
    minimal instance built automatically from the model's fields. If none
    of those work, that model's change-view check is skipped with an
    ``AdminSmokeWarning`` rather than failing the suite.

    Host projects can customize:

    - ``admin_site``: test a custom ``AdminSite`` instead of the default.
    - ``allowed_status_codes``: the default allowed status set.
    - ``model_allowed_status_codes``: per-model overrides, e.g. for admins
      that intentionally deny access (``{MyModel: {403}}``).
    - ``user_factory``: a zero-argument callable returning the user used to
      authenticate requests, for projects with a non-default
      ``AUTH_USER_MODEL``. Defaults to creating a disposable superuser.

    Exclude this test entirely under ``manage.py test`` with
    ``--exclude-tag=django_admin_tests``.
    """

    admin_site = admin.site
    allowed_status_codes = DEFAULT_ALLOWED_STATUS_CODES
    model_allowed_status_codes = {}
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

    def _assert_allowed_status(self, model, view_name, response):
        allowed = self.model_allowed_status_codes.get(model, self.allowed_status_codes)
        self.assertIn(
            response.status_code,
            allowed,
            msg=(
                f"{model.__name__} {view_name} view returned "
                f"{response.status_code}, expected one of {sorted(allowed)}"
            ),
        )

    def test_admin_smoke_changelist_returns_200(self):
        """Every registered ModelAdmin's changelist view returns an allowed status."""
        for model in self.admin_site._registry:
            with self.subTest(model=model):
                url = self._reverse_admin_url(model, "changelist")
                response = self.client.get(url)
                self._assert_allowed_status(model, "changelist", response)

    def test_admin_smoke_add_view_returns_200(self):
        """Every registered ModelAdmin's add view returns an allowed status."""
        for model in self.admin_site._registry:
            with self.subTest(model=model):
                url = self._reverse_admin_url(model, "add")
                response = self.client.get(url)
                self._assert_allowed_status(model, "add", response)

    def test_admin_smoke_change_view_returns_200(self):
        """Every registered ModelAdmin's change view returns an allowed status.

        Models for which no instance can be produced are skipped with an
        ``AdminSmokeWarning`` rather than failing.
        """
        for model in self.admin_site._registry:
            with self.subTest(model=model):
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
                response = self.client.get(url)
                self._assert_allowed_status(model, "change", response)
