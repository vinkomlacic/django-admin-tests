"""Dogfoods AdminSmokeTestCase against testapp (this repo's own test suite)."""

import unittest

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import override_settings

from django_admin_tests import testcases as admin_smoke_testcases
from tests.custom_admin_site_urls import custom_admin_site
from testapp.models import Category, RestrictedItem


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
