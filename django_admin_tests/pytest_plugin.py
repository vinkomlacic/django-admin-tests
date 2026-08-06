"""Optional pytest11 plugin for zero-config discovery of AdminSmokeTestCase
based tests.

Only loaded by pytest when django-admin-tests is installed in a
pytest-django project; never imported by django_admin_tests/testcases.py or
the manage.py test path. Implementation lands in the pytest-plugin work
item.
"""
