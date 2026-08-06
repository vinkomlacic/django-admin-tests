"""In-house minimal-instance builder used to exercise admin change views.

Deliberately dependency-free: no model_bakery or similar. Given a model,
``build_instance`` fills every field that must have a value at save time
with a naive, type-appropriate default and saves the result. Models it
can't satisfy raise ``InstanceBuildError``, which callers turn into a
skipped check rather than a failure.
"""

import datetime
import itertools
import uuid

from django.db import models
from django.utils import timezone

_counter = itertools.count(1)


class AdminSmokeWarning(UserWarning):
    """Warned when a change view can't be smoke-tested and is skipped.

    Subclasses UserWarning so consumers can filter it, e.g.
    ``warnings.simplefilter("ignore", AdminSmokeWarning)``.
    """


class InstanceBuildError(Exception):
    """Raised when no minimal instance of a model can be constructed."""


def _needs_value(field):
    """Whether a field must be given a value for save() to succeed."""
    if field.primary_key or isinstance(field, models.AutoField):
        return False
    if isinstance(field, models.ManyToManyField):
        return False
    if field.null or field.has_default():
        return False
    # auto_now/auto_now_add fields populate themselves in pre_save.
    if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
        return False
    return True


def _string_value(field, counter):
    value = f"smoke-{counter}"
    max_length = getattr(field, "max_length", None)
    if max_length is not None and len(value) > max_length:
        value = value[:max_length]
    return value


def value_for_field(field, counter=None, _building=None):
    """Return a naive, save-safe value for ``field``.

    ``choices`` wins over field type — an arbitrary type-based value would
    fail model validation on a field that constrains its values.
    """
    if counter is None:
        counter = next(_counter)

    if field.choices:
        return _first_choice(field)

    # Relations recurse; order matters since these aren't CharField subclasses.
    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
        return _related_instance(field, _building)

    # Most-specific field types first: EmailField/URLField/SlugField all
    # subclass CharField, so checking CharField first would swallow them.
    if isinstance(field, models.EmailField):
        return f"smoke-{counter}@example.com"
    if isinstance(field, models.URLField):
        return f"https://example.com/{counter}"
    if isinstance(field, models.SlugField):
        return _string_value(field, counter)
    if isinstance(field, models.GenericIPAddressField):
        return "127.0.0.1"
    if isinstance(field, models.UUIDField):
        return uuid.uuid4()
    if isinstance(field, models.BooleanField):
        return False
    # timezone.now() respects USE_TZ; a hardcoded aware datetime would warn
    # (and a naive one would warn the other way) depending on the setting.
    if isinstance(field, models.DateTimeField):
        return timezone.now()
    if isinstance(field, models.DateField):
        return timezone.now().date()
    if isinstance(field, models.TimeField):
        return timezone.now().time()
    if isinstance(field, models.DurationField):
        return datetime.timedelta()
    if isinstance(field, models.JSONField):
        return {}
    if isinstance(field, models.BinaryField):
        return b""
    if isinstance(field, models.FileField):
        return ""
    if isinstance(field, (models.DecimalField, models.FloatField)):
        return 0
    if isinstance(field, models.IntegerField):
        # Unique integer fields would collide across repeated builds.
        return counter if field.unique else 0
    if isinstance(field, (models.CharField, models.TextField)):
        return _string_value(field, counter)

    raise InstanceBuildError(
        f"No default value known for {field.model.__name__}.{field.name} "
        f"({type(field).__name__})"
    )


def _first_choice(field):
    value, label = field.choices[0]
    # Grouped choices look like ("Group", [(value, label), ...]) — it's the
    # *label* slot that holds the nested pairs, not the value slot.
    if isinstance(label, (list, tuple)):
        return label[0][0]
    return value


def _related_instance(field, _building):
    related_model = field.related_model
    existing = related_model._default_manager.first()
    if existing is not None:
        return existing
    return build_instance(related_model, _building=_building)


def build_instance(model, _building=None):
    """Build and save a minimal instance of ``model``.

    Raises ``InstanceBuildError`` if the model can't be satisfied — most
    commonly a non-nullable self-referential or circular foreign key with
    no existing row to point at.
    """
    if _building is None:
        _building = set()

    if model in _building:
        raise InstanceBuildError(
            f"Circular required foreign key involving {model.__name__}; "
            f"cannot build an instance without an existing row"
        )

    _building = _building | {model}
    counter = next(_counter)
    values = {}

    for field in model._meta.concrete_fields:
        if not _needs_value(field):
            continue
        values[field.name] = value_for_field(field, counter, _building)

    instance = model(**values)
    try:
        instance.save()
    except Exception as exc:
        raise InstanceBuildError(
            f"Could not save a minimal {model.__name__} instance: {exc}"
        ) from exc
    return instance
