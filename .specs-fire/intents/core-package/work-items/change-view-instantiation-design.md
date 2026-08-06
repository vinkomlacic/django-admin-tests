---
work_item: change-view-instantiation
intent: core-package
created: 2026-08-06T21:26:43Z
mode: validate
checkpoint_1: approved
---

# Design: In-house auto-instantiator for change-view testing

## Summary

Extend `AdminSmokeTestCase` with a third test method covering change
views. For each registered `ModelAdmin`, an instance is resolved in this
order: **registered factory → existing DB row → auto-built minimal
instance**. If all three fail to produce a saved instance, that admin's
change-view check is *skipped* (via `self.skipTest` inside the `subTest`)
with a `warnings.warn` naming the model — never a hard failure. The
auto-builder is entirely in-house: no `model_bakery` or other third-party
dependency.

## Scope

**In Scope:**
- `test_admin_smoke_change_view_returns_200` on `AdminSmokeTestCase`
- In-house minimal-instance builder with a field-type → value mapping
- FK/O2O resolution, including cycle and self-reference detection
- `register_factory(Model, callable)` module-level registry, exported from the package root
- Graceful skip + `AdminSmokeWarning` when no instance can be produced
- A genuinely unbuildable `testapp` model to exercise the skip path

**Out of Scope:**
- M2M population (not required at save time; change view renders fine without)
- Auto-detecting requirements of custom `save()`/`clean()` overrides — `register_factory` is the escape hatch
- Populating real files for `FileField`/`ImageField`

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Registry location | Module-level dict in `factories.py`, keyed by model class | Works without requiring `INSTALLED_APPS` registration; an AppConfig-based registry would couple the feature to app loading that the smoke test doesn't otherwise need |
| Factory contract | Zero-arg callable returning an instance; saved automatically if `pk is None` | Mirrors `user_factory` from `admin-smoke-testcase-core`; forgiving about the save since this is test tooling |
| Instance resolution order | factory → `_default_manager.first()` → auto-build | Explicit user intent wins; reusing a real row (host project fixtures) is cheaper and more representative than fabricating one |
| Field selection | Fill only fields where `not null`, `not has_default()`, not auto-pk, not `auto_now`/`auto_now_add`, not M2M | Anything else either already has a value or is populated by Django at save time |
| Value mapping precedence | `choices` first, then most-specific field type | An invalid choice breaks model validation; and e.g. `EmailField` subclasses `CharField`, so specificity order matters |
| Uniqueness strategy | Monotonic counter baked into generated string/int values | Avoids `unique=True` collisions when more than one row is built in a run |
| FK handling | Reuse `related._default_manager.first()`, else recurse with a `_building` set for cycle detection | Non-null cyclic/self-referential FKs are genuinely unsatisfiable from an empty table — raising is correct, and lands on the skip+warning path |
| Skip mechanism | `warnings.warn(AdminSmokeWarning)` + `self.skipTest()` inside the `subTest` | Both stdlib/Django only (no pytest); a custom warning subclass lets consumers filter it |

## Module Layout

| Module | Contents | Django imports |
|--------|----------|----------------|
| `django_admin_tests/factories.py` | `register_factory` / `unregister_factory` / `clear_factories` / `get_factory` + the module-level dict | None (pure Python) |
| `django_admin_tests/instantiation.py` | `build_instance(model)`, field→value mapping, FK/cycle handling, `AdminSmokeWarning` | `django.db.models` |
| `django_admin_tests/__init__.py` | Re-exports `register_factory`, `clear_factories` | None |

Keeping the registry free of Django imports means `__init__.py` stays safe
to import at app-load time, while the Django-dependent builder lives in its
own module.

## Field → Value Mapping

| Field type | Value |
|------------|-------|
| any field with `choices` | first valid choice |
| `CharField` / `TextField` / `SlugField` | counter-suffixed string, truncated to `max_length` |
| `EmailField` | `smoke-N@example.com` |
| `URLField` | `https://example.com/N` |
| `UUIDField` | `uuid4()` |
| `GenericIPAddressField` | `127.0.0.1` |
| `IntegerField` family | `0` (counter when `unique=True`) |
| `DecimalField` / `FloatField` | `0` |
| `BooleanField` | `False` |
| `DateField` | today |
| `DateTimeField` | now |
| `TimeField` | now.time() |
| `DurationField` | `timedelta()` |
| `JSONField` | `{}` |
| `BinaryField` | `b""` |
| `FileField` / `ImageField` | `""` |
| `ForeignKey` / `OneToOneField` | recurse (reuse existing row first) |

## Technical Approach

### Architecture

```
AdminSmokeTestCase.test_admin_smoke_change_view_returns_200
        │
        ├─ _get_change_view_instance(model)
        │       ├─ factories.get_factory(model)      → call it, save if unsaved
        │       ├─ model._default_manager.first()    → reuse existing row
        │       └─ instantiation.build_instance(model)
        │               ├─ for each required concrete field → value_for_field()
        │               └─ FK/O2O → reuse related.first() else recurse
        │                          (guarded by a `_building` set → cycle detection)
        │
        ├─ instance resolved  → GET change URL → _assert_allowed_status
        └─ all paths failed   → warnings.warn(AdminSmokeWarning) + self.skipTest()
```

## Data Models Affected

### Creates

- **`testapp.SelfReferentialItem`**: `name`, `parent` (non-null self-FK) —
  genuinely unbuildable from an empty table, providing a real skip+warning
  fixture rather than a contrived mock. Requires a migration.

## Affected Files

| File | Action | Purpose |
|------|--------|---------|
| `django_admin_tests/factories.py` | Create | Factory registry + public registration API |
| `django_admin_tests/instantiation.py` | Create | In-house minimal-instance builder, `AdminSmokeWarning` |
| `django_admin_tests/__init__.py` | Modify | Re-export `register_factory`, `clear_factories` |
| `django_admin_tests/testcases.py` | Modify | `_reverse_admin_url` gains `args`; add `_get_change_view_instance` and `test_admin_smoke_change_view_returns_200` |
| `testapp/models.py` | Modify | Add `SelfReferentialItem` |
| `testapp/admin.py` | Modify | Register `SelfReferentialItemAdmin` |
| `testapp/migrations/0002_*.py` | Create | Migration for the new model |
| `tests/test_instantiation.py` | Create | Builder unit tests: field mapping, FK reuse/recursion, cycle detection |
| `tests/test_factories.py` | Create | Registry tests: registration, precedence, validation, cleanup |
| `tests/test_admin_smoke.py` | Modify | Change-view success path, factory precedence, skip+warning path |

## Security Considerations

- **No new dependency surface**: the builder is in-house, so no third-party
  code is pulled into consumers' test runs (an explicit constraint of this
  intent).
- **Rows are transaction-scoped**: everything the builder creates lives
  inside `TestCase`'s per-test transaction and rolls back.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auto-built rows pollute the test DB | Low | `TestCase` wraps each test in a transaction that rolls back |
| Models with custom `save()`/`clean()` requiring more than field defaults | Medium | Failure → skip+warning (the designed graceful path), plus `register_factory` as the documented escape hatch |
| `unique=True` collisions across multiple built rows | Low | Monotonic counter baked into generated string/int values |
| `ImageField` change-view rendering with a non-existent file | Low | GET only renders the widget; `register_factory` covers a real consumer hitting this |
| Global mutable registry leaks between tests | Medium | `clear_factories()` provided and used in this repo's own test teardown |

## Implementation Checklist

- [ ] `factories.py`: registry dict + `register_factory`/`unregister_factory`/`clear_factories`/`get_factory`, with validation
- [ ] `instantiation.py`: `AdminSmokeWarning`, field→value mapping, `build_instance` with `_building` cycle guard and counter
- [ ] `__init__.py`: re-export `register_factory`, `clear_factories`
- [ ] `testcases.py`: `_reverse_admin_url` gains `args`; `_get_change_view_instance`; `test_admin_smoke_change_view_returns_200`
- [ ] `testapp`: add `SelfReferentialItem` + admin + migration
- [ ] Tests: success path (Category/Product/EmptyOnlyModel), factory precedence, existing-row reuse, skip+warning path, cycle detection, `no pytest import` still passing
- [ ] Verify under `pytest` and `manage.py test`; ruff; wheel build

---
*Generated by specs.md - fabriqa.ai FIRE Flow | Checkpoint 1 approved: 2026-08-06T21:26:43Z*
