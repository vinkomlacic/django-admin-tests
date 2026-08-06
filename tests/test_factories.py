"""Tests for the per-model factory registry."""

import pytest

from django_admin_tests.factories import (
    clear_factories,
    get_factory,
    register_factory,
    unregister_factory,
)
from testapp.models import Category


def test_register_and_get_factory():
    def factory():
        return Category(name="from-factory")

    register_factory(Category, factory)

    assert get_factory(Category) is factory


def test_get_factory_returns_none_when_unregistered():
    assert get_factory(Category) is None


def test_register_factory_rejects_non_callable():
    with pytest.raises(TypeError):
        register_factory(Category, "not callable")


def test_unregister_factory():
    register_factory(Category, lambda: Category(name="x"))

    assert unregister_factory(Category) is True
    assert get_factory(Category) is None
    assert unregister_factory(Category) is False


def test_clear_factories():
    register_factory(Category, lambda: Category(name="x"))

    clear_factories()

    assert get_factory(Category) is None


def test_register_factory_is_exported_from_package_root():
    import django_admin_tests

    assert django_admin_tests.register_factory is register_factory
    assert django_admin_tests.clear_factories is clear_factories
