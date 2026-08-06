"""Dogfoods AdminSmokeTestCase against testapp (this repo's own test suite)."""

import unittest
import warnings

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.db import connection
from django.test import override_settings

from django_admin_tests import testcases as admin_smoke_testcases
from django_admin_tests.factories import register_factory
from django_admin_tests.instantiation import AdminSmokeWarning
from tests.custom_admin_site_urls import custom_admin_site
from testapp.models import Category, RestrictedItem, SelfReferentialItem


class AdminSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
    """Runs the shipped smoke tests against testapp's registered admins.

    Note: the base class is accessed via the `admin_smoke_testcases` module
    attribute rather than imported by name — binding AdminSmokeTestCase
    directly at module level would make unittest/pytest discovery collect
    and run the *base* class too (it scans the whole module namespace for
    TestCase subclasses, not just ones defined here), and the base class
    has no RestrictedItem override so it would fail on the 403.

    RestrictedItem's admin unconditionally denies access (see
    testapp/admin.py), so its changelist/add views return 403 rather than
    200 — model_allowed_status_codes documents that as expected, exercising
    the per-model override mechanism.

    SelfReferentialItem is deliberately unbuildable (required self-FK), so
    its change-view check is skipped with an AdminSmokeWarning rather than
    failing — see test_admin_smoke_change_view_skips_unbuildable_model.
    """

    model_allowed_status_codes = {RestrictedItem: {403}}


@pytest.mark.django_db
def test_admin_smoke_testcase_detects_broken_admin_view():
    """A genuinely broken admin view causes AdminSmokeTestCase to fail.

    Temporarily breaks CategoryAdmin.get_queryset (restored in `finally`)
    and drives AdminSmokeTestCase's lifecycle manually, since we need to
    inspect whether the test failed rather than let an assertion propagate
    through a normal test invocation.

    Invoke the case via `case(result)`, NOT `case.run(result)`: Django's
    SimpleTestCase does its per-test setup (including creating
    `self.client`) in `_pre_setup`, which `__call__` triggers and `run`
    does not. Using `run` here makes the case error out on a missing
    `client` attribute, which would make this test pass for entirely the
    wrong reason — hence the assertion below checks *why* it failed, not
    merely that it did.
    """
    category_admin = admin.site._registry[Category]
    original_get_queryset = category_admin.__class__.get_queryset

    def broken_get_queryset(self, request):
        raise RuntimeError("boom")

    category_admin.__class__.get_queryset = broken_get_queryset
    try:
        AdminSmokeTest.setUpClass()
        try:
            case = AdminSmokeTest("test_admin_smoke_changelist_returns_200")
            result = unittest.TestResult()
            case(result)
            assert not result.wasSuccessful()
            reported = "".join(
                traceback for _, traceback in result.failures + result.errors
            )
            assert "boom" in reported, reported
        finally:
            AdminSmokeTest.tearDownClass()
    finally:
        category_admin.__class__.get_queryset = original_get_queryset


@pytest.mark.django_db
def test_admin_smoke_handles_empty_registry():
    """An AdminSite with zero registered admins passes trivially, not errors.

    Defines the subclass locally (inside the test function) rather than at
    module level so it isn't separately picked up by unittest/pytest
    discovery — it only needs to run once, driven manually here.
    """
    empty_site = AdminSite(name="admin_smoke_empty_test")

    class EmptySiteAdminSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        admin_site = empty_site

    EmptySiteAdminSmokeTest.setUpClass()
    try:
        case = EmptySiteAdminSmokeTest("test_admin_smoke_changelist_returns_200")
        result = unittest.TestResult()
        case(result)
        assert result.wasSuccessful()
        assert result.testsRun == 1
    finally:
        EmptySiteAdminSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_admin_smoke_supports_custom_admin_site():
    """A custom, non-default-named AdminSite resolves URLs correctly.

    Proves _reverse_admin_url's use of admin_site.name (rather than a
    hardcoded "admin" namespace) actually works, not just for the default
    site. Uses a dedicated URLconf (tests/custom_admin_site_urls.py) since
    the custom site's URLs aren't wired into tests/urls.py.
    """

    class CustomSiteAdminSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        admin_site = custom_admin_site

    with override_settings(ROOT_URLCONF="tests.custom_admin_site_urls"):
        CustomSiteAdminSmokeTest.setUpClass()
        try:
            case = CustomSiteAdminSmokeTest("test_admin_smoke_changelist_returns_200")
            result = unittest.TestResult()
            case(result)
            assert result.wasSuccessful(), result.failures + result.errors
            assert result.testsRun == 1
        finally:
            CustomSiteAdminSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_admin_smoke_change_view_skips_unbuildable_model():
    """An unbuildable model is skipped with a warning, not failed.

    SelfReferentialItem has a required self-FK, so no instance can be
    built from an empty table. The change-view check must record a skip
    (not a failure) and warn, naming the model.
    """
    AdminSmokeTest.setUpClass()
    try:
        case = AdminSmokeTest("test_admin_smoke_change_view_returns_200")
        result = unittest.TestResult()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", AdminSmokeWarning)
            case(result)

        assert result.wasSuccessful(), result.failures + result.errors

        skipped_models = [reason for _, reason in result.skipped]
        assert any("SelfReferentialItem" in reason for reason in skipped_models), (
            skipped_models
        )

        warned = [
            str(w.message) for w in caught if issubclass(w.category, AdminSmokeWarning)
        ]
        assert any("SelfReferentialItem" in message for message in warned), warned
    finally:
        AdminSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_admin_smoke_change_view_uses_registered_factory():
    """A registered factory takes precedence and covers an otherwise-skipped model."""
    created = {}

    def selfreferential_factory():
        # Seeding a required self-FK needs FK checks briefly relaxed —
        # exactly the kind of model-specific knowledge the auto-builder
        # can't have, and why register_factory exists.
        with connection.constraint_checks_disabled():
            root = SelfReferentialItem(name="factory-root", parent_id=1)
            root.save()
            SelfReferentialItem.objects.filter(pk=root.pk).update(parent_id=root.pk)
        root.refresh_from_db()
        created["instance"] = root
        return root

    register_factory(SelfReferentialItem, selfreferential_factory)

    AdminSmokeTest.setUpClass()
    try:
        case = AdminSmokeTest("test_admin_smoke_change_view_returns_200")
        result = unittest.TestResult()
        case(result)

        assert result.wasSuccessful(), result.failures + result.errors
        assert "instance" in created, "registered factory was never called"
        skipped_models = [reason for _, reason in result.skipped]
        assert not any("SelfReferentialItem" in r for r in skipped_models), (
            skipped_models
        )
    finally:
        AdminSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_change_view_instance_resolution_order():
    """Factory beats an existing row, which beats auto-building."""
    case = AdminSmokeTest("test_admin_smoke_change_view_returns_200")

    # 3. auto-build when nothing else is available
    built = case._get_change_view_instance(Category)
    assert built.pk is not None

    # 2. existing row preferred over building another
    existing = case._get_change_view_instance(Category)
    assert existing.pk == built.pk
    assert Category.objects.count() == 1

    # 1. registered factory wins over the existing row
    from_factory = Category.objects.create(name="from-factory")
    register_factory(Category, lambda: from_factory)
    assert case._get_change_view_instance(Category).pk == from_factory.pk


@pytest.mark.django_db
def test_allowed_status_codes_resolution_order():
    """Class attribute beats Django settings, which beat the built-in default."""
    case = AdminSmokeTest("test_admin_smoke_changelist_returns_200")

    # AdminSmokeTest sets model_allowed_status_codes for RestrictedItem.
    assert case._allowed_status_codes_for(RestrictedItem) == {403}

    # No class-level opinion on Category -> built-in default.
    assert case._allowed_status_codes_for(Category) == {200}

    # Settings fill in where the class is silent...
    with override_settings(ADMIN_TESTS_ALLOWED_STATUS_CODES=[201]):
        assert case._allowed_status_codes_for(Category) == {201}

    # ...but a class-level per-model override still wins over settings.
    with override_settings(
        ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES={"testapp.RestrictedItem": [418]}
    ):
        assert case._allowed_status_codes_for(RestrictedItem) == {403}

    # Settings per-model override applies where the class is silent.
    with override_settings(
        ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES={"testapp.Category": [418]}
    ):
        assert case._allowed_status_codes_for(Category) == {418}


@pytest.mark.django_db
def test_excluded_models_are_not_smoke_tested():
    """Both the class attribute and the settings-based exclusion drop a model."""
    case = AdminSmokeTest("test_admin_smoke_changelist_returns_200")

    assert Category in set(case._smoke_tested_models())

    with override_settings(ADMIN_TESTS_EXCLUDE=["testapp.Category"]):
        assert Category not in set(case._smoke_tested_models())

    class ExcludingSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        excluded_models = {Category}

    excluding_case = ExcludingSmokeTest("test_admin_smoke_changelist_returns_200")
    assert Category not in set(excluding_case._smoke_tested_models())
