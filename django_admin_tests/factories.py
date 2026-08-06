"""Registry of per-model factories used to build change-view test objects.

Deliberately free of Django imports so ``django_admin_tests/__init__.py``
stays safe to import while the app registry is still loading.
"""

_FACTORY_REGISTRY = {}


def register_factory(model, factory):
    """Register ``factory`` as the way to build instances of ``model``.

    ``factory`` is a zero-argument callable returning a model instance. If
    the returned instance is unsaved, ``AdminSmokeTestCase`` saves it
    before using it. A registered factory takes precedence over both
    existing rows and the built-in auto-instantiator.
    """
    if not callable(factory):
        raise TypeError(
            f"factory for {model!r} must be callable, got {type(factory).__name__}"
        )
    _FACTORY_REGISTRY[model] = factory


def unregister_factory(model):
    """Remove ``model``'s registered factory, if any. Returns True if one was removed."""
    return _FACTORY_REGISTRY.pop(model, None) is not None


def clear_factories():
    """Remove every registered factory.

    Useful in test teardown — the registry is module-level global state, so
    registrations otherwise leak between tests.
    """
    _FACTORY_REGISTRY.clear()


def get_factory(model):
    """Return the factory registered for ``model``, or None."""
    return _FACTORY_REGISTRY.get(model)
