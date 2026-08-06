"""Shared pytest fixtures for this repo's own test suite (see testing-standards.md)."""

import pytest

from django_admin_tests.factories import clear_factories


@pytest.fixture(autouse=True)
def _clear_factory_registry():
    """Keep the module-level factory registry from leaking between tests.

    Autouse because the registry is global mutable state — a test that
    registers a factory would otherwise silently change the behavior of
    every test after it.
    """
    clear_factories()
    yield
    clear_factories()
