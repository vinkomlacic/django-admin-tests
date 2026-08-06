"""Tests verifying the package skeleton is correctly scaffolded."""

import ast
from pathlib import Path

import django_admin_tests
from django_admin_tests.apps import DjangoAdminTestsConfig


def test_version_is_set():
    assert django_admin_tests.__version__


def test_apps_config_name():
    assert DjangoAdminTestsConfig.name == "django_admin_tests"


def test_testcases_module_never_imports_pytest():
    package_dir = Path(django_admin_tests.__file__).parent
    source = package_dir.joinpath("testcases.py").read_text()
    tree = ast.parse(source)

    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".")[0])

    assert "pytest" not in imported_names
