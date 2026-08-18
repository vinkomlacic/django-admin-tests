"""Dogfoods AdminSmokeTestCase against testapp (this repo's own test suite)."""

import unittest
import warnings

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import override_settings

from django_admin_tests import testcases as admin_smoke_testcases
from django_admin_tests.factories import register_factory
from django_admin_tests.instantiation import AdminSmokeWarning
from django_admin_tests.testcases import EMPTY_REGISTRY_METHOD_NAME, VIEW_NAMES
from tests.custom_admin_site_urls import custom_admin_site
from testapp.models import Category, RestrictedItem, SelfReferentialItem, SluggedArticle

# Generated method names. Tests that only need a case *instance* (to reach a
# helper) still have to name a real method — TestCase("nonexistent") raises
# ValueError — so they use one of these rather than a made-up name.
CATEGORY_CHANGELIST = "test_admin_smoke_testapp_category_changelist"
CATEGORY_CHANGE = "test_admin_smoke_testapp_category_change"
PRODUCT_CHANGELIST = "test_admin_smoke_testapp_product_changelist"
SLUGGED_ARTICLE_ADD = "test_admin_smoke_testapp_sluggedarticle_add"
SELF_REFERENTIAL_CHANGE = "test_admin_smoke_testapp_selfreferentialitem_change"


class AdminSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
    """Runs the shipped smoke tests against testapp's registered admins.

    Note: the base class is accessed via the `admin_smoke_testcases` module
    attribute rather than imported by name — binding AdminSmokeTestCase
    directly at module level would make unittest/pytest discovery collect
    and run the *base* class too (it scans the whole module namespace for
    TestCase subclasses, not just ones defined here), and the base class
    has no RestrictedItem override so it would fail on the 403.

    This class is where the positive path lives: one generated method per
    (registered model, view), all collected and run normally.

    RestrictedItem's admin unconditionally denies access (see
    testapp/admin.py), so its changelist/add views return 403 rather than
    200 — model_allowed_status_codes documents that as expected, exercising
    the per-model override mechanism.

    SelfReferentialItem is deliberately unbuildable (required self-FK), so
    its change-view check is skipped with an AdminSmokeWarning rather than
    failing — see test_admin_smoke_change_view_skips_unbuildable_model.
    """

    model_allowed_status_codes = {RestrictedItem: {403}}


def _expected_names(site):
    return {
        f"test_admin_smoke_{model._meta.app_label}_{model._meta.model_name}_{view}"
        for model in site._registry
        for view in VIEW_NAMES
    }


def _collected(test_case_class):
    return set(unittest.TestLoader().getTestCaseNames(test_case_class))


# --------------------------------------------------------------------------
# Method generation
# --------------------------------------------------------------------------


def test_one_method_is_generated_per_model_and_view():
    """The registry is covered exactly: models x views, no more, no less."""
    expected = _expected_names(admin.site)

    assert _collected(AdminSmokeTest) == expected
    assert len(expected) == len(admin.site._registry) * len(VIEW_NAMES)


def test_base_class_itself_carries_generated_methods():
    """Generation must not depend on being subclassed.

    The pytest plugin collects the installed testcases module directly, so
    AdminSmokeTestCase itself has to carry the tests. This is the trap
    __init_subclass__ would have fallen into — it doesn't fire for the class
    that defines it.
    """
    assert _collected(admin_smoke_testcases.AdminSmokeTestCase) == _expected_names(
        admin.site
    )


def test_generated_methods_are_named_and_documented():
    """Reports identify the model/view, rather than showing a generic name."""
    method = getattr(AdminSmokeTest, CATEGORY_CHANGELIST)

    assert method.__name__ == CATEGORY_CHANGELIST
    assert method.__qualname__ == f"AdminSmokeTest.{CATEGORY_CHANGELIST}"
    assert "testapp.Category changelist" in method.__doc__


def test_narrowing_subclass_drops_methods_inherited_from_the_parent_site():
    """A subclass with its own AdminSite must not run the parent's models.

    custom_admin_site registers only Category, so the 21 methods generated
    for the default site's other models would resolve URLs against the wrong
    namespace. They're shadowed with None, which both unittest's loader and
    pytest's unittest collector filter out.
    """

    class CustomSiteSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        admin_site = custom_admin_site

    assert _collected(CustomSiteSmokeTest) == _expected_names(custom_admin_site)
    assert len(_collected(CustomSiteSmokeTest)) == len(VIEW_NAMES)
    assert getattr(CustomSiteSmokeTest, PRODUCT_CHANGELIST) is None


def test_host_authored_test_methods_are_never_shadowed():
    """Only methods we generated are eligible for neutralizing."""

    class HostSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        admin_site = custom_admin_site

        def test_host_authored_check(self):
            pass

    assert "test_host_authored_check" in _collected(HostSmokeTest)


def test_explicitly_defined_method_wins_over_the_generated_one():
    """A host overriding one model's check keeps their own implementation.

    Generation would otherwise setattr straight over it, silently discarding
    what they wrote.
    """
    called = {}

    class OverridingSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        def test_admin_smoke_testapp_category_changelist(self):
            called["mine"] = True

    OverridingSmokeTest().test_admin_smoke_testapp_category_changelist()

    assert called == {"mine": True}
    # ...and it must not be treated as ours to neutralize later.
    assert CATEGORY_CHANGELIST not in OverridingSmokeTest._admin_smoke_generated

    class NarrowerStill(OverridingSmokeTest):
        admin_site = custom_admin_site

    assert callable(getattr(NarrowerStill, CATEGORY_CHANGELIST))


def test_metaclass_generates_nothing_without_an_admin_site():
    """The metaclass stays inert on a class that names no site to inspect."""

    class NoSite(metaclass=admin_smoke_testcases.AdminSmokeMeta):
        pass

    assert not hasattr(NoSite, "_admin_smoke_generated")


def test_colliding_generated_names_raise_rather_than_dropping_a_model():
    """Ambiguous app_label/model_name pairs fail loudly.

    app "foo_bar" + model "baz" and app "foo" + model "bar_baz" both render
    as ..._foo_bar_baz_changelist. Silently letting one overwrite the other
    would drop a model's coverage without a word.
    """

    class StubMeta:
        def __init__(self, app_label, model_name):
            self.app_label = app_label
            self.model_name = model_name
            self.label = f"{app_label}.{model_name}"

    class StubModel:
        def __init__(self, app_label, model_name):
            self._meta = StubMeta(app_label, model_name)

    class StubSite:
        def __init__(self, models):
            self._registry = {model: None for model in models}

    site = StubSite([StubModel("foo_bar", "baz"), StubModel("foo", "bar_baz")])

    with pytest.raises(ImproperlyConfigured, match="both map to"):
        admin_smoke_testcases._build_generated_tests(site)


# --------------------------------------------------------------------------
# Behavior of the generated tests
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_admin_smoke_testcase_detects_broken_admin_view():
    """A genuinely broken admin view causes its own test to fail.

    Temporarily breaks CategoryAdmin.get_queryset (restored in `finally`)
    and drives the case's lifecycle manually, since we need to inspect
    whether the test failed rather than let an assertion propagate through a
    normal test invocation.

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
            case = AdminSmokeTest(CATEGORY_CHANGELIST)
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
def test_admin_smoke_reports_fieldset_keyerror_clearly():
    """A field named in `fieldsets` but missing from the ModelForm fails
    clearly, not with a bare KeyError (GitHub issue #1).

    SluggedArticle.slug is required at the DB level but populated in
    save(), so SluggedArticleAdmin excludes it from the form — that alone
    is valid (see AdminSmokeTest, which smoke-tests it clean). Temporarily
    adding a `fieldsets` entry that still names the excluded field is a
    ModelAdmin misconfiguration Django's own system checks don't catch
    (readonly_fields is where you're supposed to list it instead); it only
    surfaces as `KeyError: "Key 'slug' not found in ..."` when the form is
    actually rendered. AdminSmokeTestCase must translate that into a
    failure naming the model, per coding-standards.md's precedent for
    NoReverseMatch.
    """
    slugged_admin = admin.site._registry[SluggedArticle]
    original_fieldsets = slugged_admin.__class__.fieldsets
    slugged_admin.__class__.fieldsets = ((None, {"fields": ("name", "slug")}),)

    try:
        AdminSmokeTest.setUpClass()
        try:
            case = AdminSmokeTest(SLUGGED_ARTICLE_ADD)
            result = unittest.TestResult()
            case(result)

            assert not result.wasSuccessful()
            assert result.errors == [], result.errors
            reported = "".join(traceback for _, traceback in result.failures)
            assert "SluggedArticle add view raised" in reported, reported
            assert "readonly_fields" in reported, reported
        finally:
            AdminSmokeTest.tearDownClass()
    finally:
        slugged_admin.__class__.fieldsets = original_fieldsets


@pytest.mark.django_db
def test_admin_smoke_handles_empty_registry():
    """An AdminSite with zero registered admins passes trivially, not errors.

    Without the placeholder such a class would generate no methods at all,
    which is indistinguishable from the smoke tests never having run.

    Defines the subclass locally (inside the test function) rather than at
    module level so it isn't separately picked up by unittest/pytest
    discovery — it only needs to run once, driven manually here.
    """
    empty_site = AdminSite(name="admin_smoke_empty_test")

    class EmptySiteAdminSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        admin_site = empty_site

    assert _collected(EmptySiteAdminSmokeTest) == {EMPTY_REGISTRY_METHOD_NAME}

    EmptySiteAdminSmokeTest.setUpClass()
    try:
        case = EmptySiteAdminSmokeTest(EMPTY_REGISTRY_METHOD_NAME)
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
            case = CustomSiteAdminSmokeTest(CATEGORY_CHANGELIST)
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
        case = AdminSmokeTest(SELF_REFERENTIAL_CHANGE)
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
        case = AdminSmokeTest(SELF_REFERENTIAL_CHANGE)
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


# --------------------------------------------------------------------------
# Exclusion — resolved per run, not when the methods were generated
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_excluded_models_are_not_smoke_tested():
    """Both the class attribute and the settings-based exclusion drop a model."""
    case = AdminSmokeTest(CATEGORY_CHANGELIST)

    assert not case._is_excluded(Category)

    with override_settings(ADMIN_TESTS_EXCLUDE=["testapp.Category"]):
        assert case._is_excluded(Category)

    class ExcludingSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        excluded_models = {Category}

    assert ExcludingSmokeTest(CATEGORY_CHANGELIST)._is_excluded(Category)


@pytest.mark.django_db
def test_excluded_model_reports_as_skipped_rather_than_vanishing():
    """An excluded model keeps its method; the method skips."""

    class ExcludingSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        excluded_models = {Category}

    assert CATEGORY_CHANGELIST in _collected(ExcludingSmokeTest)

    ExcludingSmokeTest.setUpClass()
    try:
        case = ExcludingSmokeTest(CATEGORY_CHANGELIST)
        result = unittest.TestResult()
        case(result)

        assert result.wasSuccessful(), result.failures + result.errors
        assert [reason for _, reason in result.skipped], "expected a skip"
    finally:
        ExcludingSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_settings_exclusion_applies_without_regenerating_methods():
    """override_settings still takes effect after the methods were built.

    This is the whole reason exclusion is resolved inside the generated body
    rather than when the class is created: the method set is frozen at import
    time, but the decision to run is not.
    """
    AdminSmokeTest.setUpClass()
    try:
        with override_settings(ADMIN_TESTS_EXCLUDE=["testapp.Category"]):
            case = AdminSmokeTest(CATEGORY_CHANGELIST)
            result = unittest.TestResult()
            case(result)

            assert result.wasSuccessful(), result.failures + result.errors
            assert [reason for _, reason in result.skipped], "expected a skip"
    finally:
        AdminSmokeTest.tearDownClass()


# --------------------------------------------------------------------------
# Helper-level behavior (unchanged by generation)
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_change_view_instance_resolution_order():
    """Factory beats an existing row, which beats auto-building."""
    case = AdminSmokeTest(CATEGORY_CHANGE)

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
    case = AdminSmokeTest(CATEGORY_CHANGELIST)

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
def test_user_factory_overrides_default_superuser_creation():
    """The documented escape hatch for custom AUTH_USER_MODEL projects."""
    created = {}

    def make_user():
        user = get_user_model().objects.create_superuser(
            username="from-factory",
            email="from-factory@example.com",
            password="pw",
        )
        created["user"] = user
        return user

    class FactoryUserSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        user_factory = staticmethod(make_user)
        model_allowed_status_codes = {RestrictedItem: {403}}

    FactoryUserSmokeTest.setUpClass()
    try:
        case = FactoryUserSmokeTest(CATEGORY_CHANGELIST)
        result = unittest.TestResult()
        case(result)

        assert result.wasSuccessful(), result.failures + result.errors
        assert created["user"].username == "from-factory"
        assert FactoryUserSmokeTest.admin_smoke_test_user == created["user"]
    finally:
        FactoryUserSmokeTest.tearDownClass()


@pytest.mark.django_db
def test_unsaved_factory_instance_is_saved_before_use():
    """register_factory may return an unsaved instance; we persist it."""
    case = AdminSmokeTest(CATEGORY_CHANGE)
    register_factory(Category, lambda: Category(name="unsaved"))

    instance = case._get_change_view_instance(Category)

    assert instance.pk is not None
    assert Category.objects.filter(pk=instance.pk).exists()


@pytest.mark.django_db
def test_class_level_allowed_status_codes_apply_to_all_models():
    """The class-wide override, as opposed to the per-model mapping."""

    class PermissiveSmokeTest(admin_smoke_testcases.AdminSmokeTestCase):
        allowed_status_codes = {200, 403}

    case = PermissiveSmokeTest(CATEGORY_CHANGELIST)

    assert case._allowed_status_codes_for(Category) == {200, 403}
    assert case._allowed_status_codes_for(RestrictedItem) == {200, 403}


@pytest.mark.django_db
def test_unresolvable_admin_url_fails_with_model_name():
    """A model whose admin URL can't be reversed fails clearly, not with a KeyError.

    coding-standards.md requires the offending model be named in the
    message rather than surfacing a bare lookup error.
    """
    case = AdminSmokeTest(CATEGORY_CHANGELIST)

    with pytest.raises(AssertionError, match="Could not resolve changelist URL"):
        case._reverse_admin_url(Category, "changelist", args=["too", "many", "args"])
