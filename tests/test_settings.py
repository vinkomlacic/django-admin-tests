"""Tests for the Django-settings-based configuration accessors."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_admin_tests.settings import (
    DEFAULT_ALLOWED_STATUS_CODES,
    get_allowed_status_codes,
    get_excluded_admins,
    get_model_allowed_status_codes,
    model_label,
)
from testapp.models import Category


def test_model_label_is_lowercase_app_dot_model():
    assert model_label(Category) == "testapp.category"


def test_allowed_status_codes_defaults_when_unset():
    assert get_allowed_status_codes() == DEFAULT_ALLOWED_STATUS_CODES


@override_settings(ADMIN_TESTS_ALLOWED_STATUS_CODES=[200, 302])
def test_allowed_status_codes_from_settings():
    assert get_allowed_status_codes() == {200, 302}


@override_settings(ADMIN_TESTS_ALLOWED_STATUS_CODES=[])
def test_allowed_status_codes_rejects_empty():
    with pytest.raises(ImproperlyConfigured, match="must not be empty"):
        get_allowed_status_codes()


@override_settings(ADMIN_TESTS_ALLOWED_STATUS_CODES=["not-an-int"])
def test_allowed_status_codes_rejects_non_integers():
    with pytest.raises(ImproperlyConfigured, match="integer status codes"):
        get_allowed_status_codes()


def test_model_allowed_status_codes_defaults_to_empty():
    assert get_model_allowed_status_codes() == {}


@override_settings(
    ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES={"testapp.RestrictedItem": [403]}
)
def test_model_allowed_status_codes_normalizes_labels():
    assert get_model_allowed_status_codes() == {"testapp.restricteditem": {403}}


@override_settings(ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES={"no-dot": [403]})
def test_model_allowed_status_codes_rejects_bad_label():
    with pytest.raises(ImproperlyConfigured, match="app_label.ModelName"):
        get_model_allowed_status_codes()


@override_settings(ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES=["not", "a", "dict"])
def test_model_allowed_status_codes_rejects_non_dict():
    with pytest.raises(ImproperlyConfigured, match="must be a dict"):
        get_model_allowed_status_codes()


def test_excluded_admins_defaults_to_empty():
    assert get_excluded_admins() == frozenset()


@override_settings(ADMIN_TESTS_EXCLUDE=["testapp.SelfReferentialItem"])
def test_excluded_admins_normalizes_labels():
    assert get_excluded_admins() == {"testapp.selfreferentialitem"}


@override_settings(ADMIN_TESTS_EXCLUDE=["missing-dot"])
def test_excluded_admins_rejects_bad_label():
    with pytest.raises(ImproperlyConfigured, match="app_label.ModelName"):
        get_excluded_admins()
