"""Django-settings-based configuration for the admin smoke tests.

Lets host projects configure the auto-collected tests without writing any
Python — the point of the optional pytest plugin. Every accessor tolerates
the setting being absent and returns a sensible default.

Recognized settings:

``ADMIN_TESTS_ALLOWED_STATUS_CODES``
    Iterable of ints; the globally allowed response statuses. Default {200}.

``ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES``
    Mapping of ``"app_label.ModelName"`` to an iterable of ints, overriding
    the global set for those models.

``ADMIN_TESTS_EXCLUDE``
    Iterable of ``"app_label.ModelName"`` labels to skip entirely.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_ALLOWED_STATUS_CODES = frozenset({200})

ALLOWED_STATUS_CODES_SETTING = "ADMIN_TESTS_ALLOWED_STATUS_CODES"
MODEL_ALLOWED_STATUS_CODES_SETTING = "ADMIN_TESTS_MODEL_ALLOWED_STATUS_CODES"
EXCLUDE_SETTING = "ADMIN_TESTS_EXCLUDE"


def model_label(model):
    """Return a model's canonical lookup label, e.g. ``"testapp.category"``."""
    opts = model._meta
    return f"{opts.app_label}.{opts.model_name}".lower()


def _normalize_label(label, setting_name):
    if not isinstance(label, str) or "." not in label:
        raise ImproperlyConfigured(
            f"{setting_name} keys must be 'app_label.ModelName' strings, got {label!r}"
        )
    return label.lower()


def _status_codes(value, setting_name):
    try:
        codes = frozenset(int(code) for code in value)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            f"{setting_name} must contain integer status codes: {exc}"
        ) from exc
    if not codes:
        raise ImproperlyConfigured(f"{setting_name} must not be empty")
    return codes


def get_allowed_status_codes():
    """Globally allowed status codes, or the built-in default."""
    value = getattr(settings, ALLOWED_STATUS_CODES_SETTING, None)
    if value is None:
        return DEFAULT_ALLOWED_STATUS_CODES
    return _status_codes(value, ALLOWED_STATUS_CODES_SETTING)


def get_model_allowed_status_codes():
    """Per-model allowed status codes, keyed by normalized model label."""
    value = getattr(settings, MODEL_ALLOWED_STATUS_CODES_SETTING, None)
    if not value:
        return {}
    if not isinstance(value, dict):
        raise ImproperlyConfigured(
            f"{MODEL_ALLOWED_STATUS_CODES_SETTING} must be a dict, "
            f"got {type(value).__name__}"
        )
    return {
        _normalize_label(label, MODEL_ALLOWED_STATUS_CODES_SETTING): _status_codes(
            codes, MODEL_ALLOWED_STATUS_CODES_SETTING
        )
        for label, codes in value.items()
    }


def get_excluded_admins():
    """Set of normalized model labels to skip entirely."""
    value = getattr(settings, EXCLUDE_SETTING, None)
    if not value:
        return frozenset()
    return frozenset(_normalize_label(label, EXCLUDE_SETTING) for label in value)
