"""AdminSmokeTestCase: asserts every registered ModelAdmin's changelist/add/
change views return 200 (or another allowed status).

This module must never import pytest — it has to run unmodified under both
``manage.py test`` and pytest (see coding-standards.md). Implementation lands
in the admin-smoke-testcase-core work item.
"""
