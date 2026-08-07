"""django-admin-tests: automatic admin smoke-test coverage for Django projects."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from django_admin_tests.factories import (
    clear_factories,
    register_factory,
    unregister_factory,
)

try:
    __version__ = _version("django-admin-tests")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["clear_factories", "register_factory", "unregister_factory"]
