"""django-admin-tests: automatic admin smoke-test coverage for Django projects."""

from django_admin_tests.factories import (
    clear_factories,
    register_factory,
    unregister_factory,
)

__version__ = "0.1.0.dev0"

__all__ = ["clear_factories", "register_factory", "unregister_factory"]
