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


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (models.URLField(), "https://example.com/3"),
        (models.GenericIPAddressField(), "127.0.0.1"),
        (models.FileField(), ""),
        (models.DecimalField(max_digits=5, decimal_places=2), 0),
        (models.FloatField(), 0),
    ],
)
def test_value_for_field_remaining_types(field, expected):
    assert value_for_field(field, counter=3) == expected


def test_value_for_field_generates_counter_when_not_given():
    """Callers may omit the counter; the module-level sequence supplies one."""
    first = value_for_field(models.CharField(max_length=50))
    second = value_for_field(models.CharField(max_length=50))

    assert first != second


def test_value_for_field_raises_for_unknown_field_type():
    class ExoticField(models.Field):
        pass

    field = ExoticField()
    field.set_attributes_from_name("exotic")
    field.model = type("FakeModel", (), {"__name__": "FakeModel"})

    with pytest.raises(InstanceBuildError, match="No default value known"):
        value_for_field(field, counter=1)


@pytest.mark.django_db
def test_build_instance_wraps_save_failures():
    """A model whose save() fails surfaces as InstanceBuildError, not a raw error."""

    def exploding_save(self, *args, **kwargs):
        raise RuntimeError("save blew up")

    original = Category.save
    Category.save = exploding_save
    try:
        with pytest.raises(InstanceBuildError, match="Could not save a minimal"):
            build_instance(Category)
    finally:
        Category.save = original


@pytest.mark.django_db
def test_needs_value_skips_nullable_default_and_auto_now_fields():
    """Fields Django populates itself must not be filled by the builder."""
    from django_admin_tests.instantiation import _needs_value

    assert _needs_value(models.CharField(max_length=10, null=True)) is False
    assert _needs_value(models.CharField(max_length=10, default="x")) is False
    assert _needs_value(models.DateTimeField(auto_now=True)) is False
    assert _needs_value(models.DateTimeField(auto_now_add=True)) is False
    assert _needs_value(models.ManyToManyField("self")) is False
    assert _needs_value(models.CharField(max_length=10)) is True
