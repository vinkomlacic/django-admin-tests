"""Tests for the in-house minimal-instance builder."""

import datetime
import uuid

import pytest
from django.db import models

from django_admin_tests.instantiation import (
    InstanceBuildError,
    build_instance,
    value_for_field,
)
from testapp.models import Category, EmptyOnlyModel, Product, SelfReferentialItem


@pytest.mark.django_db
def test_build_instance_plain_model():
    instance = build_instance(Category)

    assert instance.pk is not None
    assert instance.name


@pytest.mark.django_db
def test_build_instance_fills_foreign_key():
    instance = build_instance(Product)

    assert instance.pk is not None
    assert instance.category_id is not None


@pytest.mark.django_db
def test_build_instance_reuses_existing_related_row():
    existing = Category.objects.create(name="existing")

    instance = build_instance(Product)

    assert instance.category == existing
    assert Category.objects.count() == 1


@pytest.mark.django_db
def test_build_instance_from_empty_table():
    assert EmptyOnlyModel.objects.count() == 0

    instance = build_instance(EmptyOnlyModel)

    assert instance.pk is not None


@pytest.mark.django_db
def test_build_instance_raises_on_required_self_reference():
    with pytest.raises(InstanceBuildError, match="Circular required foreign key"):
        build_instance(SelfReferentialItem)


@pytest.mark.parametrize(
    ("field", "expected_type"),
    [
        (models.CharField(max_length=50), str),
        (models.TextField(), str),
        (models.SlugField(), str),
        (models.IntegerField(), int),
        (models.BooleanField(), bool),
        (models.DateField(), datetime.date),
        (models.DateTimeField(), datetime.datetime),
        (models.TimeField(), datetime.time),
        (models.DurationField(), datetime.timedelta),
        (models.UUIDField(), uuid.UUID),
        (models.JSONField(), dict),
        (models.BinaryField(), bytes),
    ],
)
def test_value_for_field_returns_expected_type(field, expected_type):
    value = value_for_field(field, counter=1)

    assert isinstance(value, expected_type)


def test_value_for_field_respects_max_length():
    field = models.CharField(max_length=4)

    value = value_for_field(field, counter=123456)

    assert len(value) <= 4


def test_value_for_field_prefers_choices_over_type():
    field = models.CharField(max_length=20, choices=[("a", "A"), ("b", "B")])

    assert value_for_field(field, counter=1) == "a"


def test_value_for_field_handles_grouped_choices():
    field = models.CharField(
        max_length=20, choices=[("Group", [("x", "X"), ("y", "Y")])]
    )

    assert value_for_field(field, counter=1) == "x"


def test_value_for_field_email_is_valid_shape():
    value = value_for_field(models.EmailField(), counter=7)

    assert "@" in value


def test_value_for_field_unique_integer_uses_counter():
    unique_value = value_for_field(models.IntegerField(unique=True), counter=42)
    plain_value = value_for_field(models.IntegerField(), counter=42)

    assert unique_value == 42
    assert plain_value == 0
