"""URLconf used only by test_admin_smoke.py to prove AdminSmokeTestCase
supports non-default AdminSite instances (see testing-standards.md's
critical-path coverage requirement for custom AdminSite instances).
"""

from django.contrib.admin.sites import AdminSite
from django.urls import path

from testapp.models import Category

custom_admin_site = AdminSite(name="custom_admin_smoke_test")
custom_admin_site.register(Category)

urlpatterns = [
    path("custom-admin/", custom_admin_site.urls),
]
