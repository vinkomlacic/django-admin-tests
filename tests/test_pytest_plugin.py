"""Tests for the optional pytest11 auto-discovery plugin."""

import pytest

from django_admin_tests import pytest_plugin


def test_plugin_is_loaded_via_entry_point(pytestconfig):
    """The pytest11 entry point makes pytest load our plugin automatically."""
    assert pytestconfig.pluginmanager.hasplugin("django_admin_tests")


def test_auto_collection_ini_defaults_to_false(pytestconfig):
    """Installing the package must not silently add tests to an existing suite.

    Also guards the config choice explained in pyproject.toml: this repo's
    testapp registers a permission-denying admin, so auto-collecting the
    un-subclassed base class here would fail. If someone flips this on,
    this test says why it broke.
    """
    assert pytestconfig.getini(pytest_plugin.AUTO_INI_NAME) is False


def test_marker_is_registered(pytestconfig):
    """Registered by the plugin so consumers don't get PytestUnknownMarkWarning."""
    markers = pytestconfig.getini("markers")

    assert any(marker.startswith(pytest_plugin.MARKER_NAME) for marker in markers)


# ---------------------------------------------------------------------------
# End-to-end: a throwaway host project that never imports django_admin_tests.
# ---------------------------------------------------------------------------

SETTINGS = """
SECRET_KEY = "django-insecure-plugin-test"
DEBUG = True
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hostapp",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "host_urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}}
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuring the auto-collected tests with no host-side Python:
ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES = {"hostapp.LockedThing": [403]}
ADMIN_TESTS_EXCLUDE = ["hostapp.IgnoredThing"]
"""

HOSTAPP_MODELS = """
from django.db import models


class Thing(models.Model):
    name = models.CharField(max_length=50)


class LockedThing(models.Model):
    name = models.CharField(max_length=50)


class IgnoredThing(models.Model):
    name = models.CharField(max_length=50)
"""

HOSTAPP_ADMIN = """
from django.contrib import admin

from hostapp.models import IgnoredThing, LockedThing, Thing

admin.site.register(Thing)


@admin.register(IgnoredThing)
class IgnoredThingAdmin(admin.ModelAdmin):
    # Deliberately broken: if ADMIN_TESTS_EXCLUDE were ignored, the smoke
    # tests would hit this and fail, so the exclusion is genuinely proven
    # rather than passing by coincidence.
    def get_queryset(self, request):
        raise RuntimeError("IgnoredThing should have been excluded")


@admin.register(LockedThing)
class LockedThingAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
"""

HOST_URLS = """
from django.contrib import admin
from django.urls import path

urlpatterns = [path("admin/", admin.site.urls)]
"""

# The host project's own test file — note it never mentions django_admin_tests.
HOST_TEST_FILE = """
def test_host_projects_own_test():
    assert True
"""

INI_TEMPLATE = """
[pytest]
DJANGO_SETTINGS_MODULE = host_settings
django_admin_tests_auto = {auto}
"""


@pytest.fixture
def host_project(pytester, monkeypatch):
    """Build a throwaway Django project in a temp dir, isolated from this one."""
    # This repo's own DJANGO_SETTINGS_MODULE would otherwise leak into the
    # subprocess and pre-configure Django before the host settings load.
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)

    hostapp = pytester.mkpydir("hostapp")
    hostapp.joinpath("models.py").write_text(HOSTAPP_MODELS)
    hostapp.joinpath("admin.py").write_text(HOSTAPP_ADMIN)

    pytester.makepyfile(host_settings=SETTINGS)
    pytester.makepyfile(host_urls=HOST_URLS)
    pytester.makepyfile(test_host_project=HOST_TEST_FILE)

    def configure(auto):
        pytester.makefile(".ini", pytest=INI_TEMPLATE.format(auto=auto))

    return configure


def test_auto_collection_runs_smoke_tests_with_no_host_imports(host_project, pytester):
    """The headline acceptance criterion, proven end to end.

    The host project's only test file knows nothing about
    django_admin_tests, yet enabling the ini flag makes the admin smoke
    tests appear and pass — including honoring the settings-based per-model
    status override and exclusion. Runs in a subprocess so this session's
    Django configuration can't leak in.
    """
    host_project(auto="true")

    result = pytester.runpytest_subprocess("-v")

    result.stdout.fnmatch_lines(["*test_admin_smoke_hostapp_thing_changelist*"])
    result.stdout.fnmatch_lines(["*test_admin_smoke_hostapp_thing_add*"])
    result.stdout.fnmatch_lines(["*test_admin_smoke_hostapp_thing_change*"])
    # 5 registered models (auth.Group, auth.User and hostapp's three) x 3
    # views = 15 injected tests, plus the host's own one. IgnoredThing is
    # excluded via settings, which now reports as 3 skips rather than as
    # three tests that never existed.
    result.assert_outcomes(passed=13, skipped=3)


def test_no_auto_collection_when_ini_flag_is_off(host_project, pytester):
    """With the flag off, only the host project's own test runs."""
    host_project(auto="false")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(passed=1)
    assert "test_admin_smoke_hostapp_thing_changelist" not in result.stdout.str()


def test_collection_failure_warns_instead_of_propagating(monkeypatch, recwarn):
    """A failure inside injection must not abort the host's whole session.

    Note this guard only covers failures in *our* collection step. A host
    project whose admin raises on import breaks django.setup() itself,
    long before this hook runs — that is Django's failure to report, not
    something this plugin can or should swallow.
    """

    def boom(session, smoke_path):
        raise RuntimeError("collection exploded")

    monkeypatch.setattr(pytest_plugin, "_collect_smoke_items", boom)

    class Config:
        @staticmethod
        def getini(name):
            return True

    items = ["existing-item"]
    pytest_plugin.pytest_collection_modifyitems(
        session=None, config=Config(), items=items
    )

    assert items == ["existing-item"], "host items must be left intact"
    assert any("could not auto-collect" in str(w.message) for w in recwarn)


def test_no_double_injection_when_module_already_collected(monkeypatch):
    """If the smoke module was already collected, don't inject it twice.

    Matches on resolved path rather than nodeid prefix, so a host project
    with its own top-level testcases.py isn't mistaken for ours.
    """
    called = []
    monkeypatch.setattr(
        pytest_plugin,
        "_collect_smoke_items",
        lambda session, smoke_path: called.append(smoke_path) or ["injected"],
    )

    class Item:
        path = pytest_plugin._smoke_module_path()

    class Config:
        @staticmethod
        def getini(name):
            return True

    items = [Item()]
    pytest_plugin.pytest_collection_modifyitems(
        session=None, config=Config(), items=items
    )

    assert len(items) == 1, "should not have injected a duplicate"
    assert called == [], "_collect_smoke_items should not have been called"
