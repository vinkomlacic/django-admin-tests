"""Verifies the dev-only testapp is correctly wired for dogfooding."""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse

from testapp.models import Category, EmptyOnlyModel, Product, RestrictedItem


def test_sample_models_registered_in_admin():
    registered = set(admin.site._registry.keys())
    assert {Category, Product, EmptyOnlyModel, RestrictedItem} <= registered


@pytest.mark.django_db
def test_empty_only_model_has_zero_rows():
    assert EmptyOnlyModel.objects.count() == 0


def test_restricted_item_admin_denies_permission():
    model_admin = admin.site._registry[RestrictedItem]
    assert model_admin.has_module_permission(request=None) is False
    assert model_admin.has_view_permission(request=None) is False
    assert model_admin.has_change_permission(request=None) is False
    assert model_admin.has_add_permission(request=None) is False
    assert model_admin.has_delete_permission(request=None) is False


@pytest.mark.django_db
def test_category_changelist_accessible_to_superuser(client):
    superuser = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )
    client.force_login(superuser)

    response = client.get(reverse("admin:testapp_category_changelist"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_restricted_item_changelist_denied_even_for_superuser(client):
    superuser = get_user_model().objects.create_superuser(
        username="admin2", email="admin2@example.com", password="password"
    )
    client.force_login(superuser)

    response = client.get(reverse("admin:testapp_restricteditem_changelist"))

    assert response.status_code == 403
