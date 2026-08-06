---
work_item: admin-smoke-testcase-core
intent: core-package
created: 2026-08-06T21:05:59Z
mode: validate
checkpoint_1: approved
---

# Design: AdminSmokeTestCase core (changelist + add views)

## Summary

A Django `TestCase` subclass, `AdminSmokeTestCase`, that iterates every
entry in a configurable `admin_site._registry`, logs in as a disposable
superuser (auto-created, or supplied via an overridable `user_factory`),
and asserts the changelist and add views for each registered `ModelAdmin`
return a status in a configurable allowed-status set (default `{200}`,
overridable globally or per-model). Contains no pytest import. Change-view
testing is explicitly deferred to the `change-view-instantiation` work
item.

## Scope

**In Scope:**
- Changelist view assertions for every registered `ModelAdmin`
- Add view assertions for every registered `ModelAdmin`
- Configurable allowed status codes (global default + per-model override)
- Configurable `AdminSite` (default `django.contrib.admin.site`)
- Configurable auth fixture (`user_factory` override for custom user models)
- `django.test.tag("django_admin_tests")` for `manage.py test --exclude-tag` support
- Dogfood tests against `testapp` proving both the positive path (200) and negative path (a genuinely broken admin gets caught)

**Out of Scope:**
- Change view assertions and object auto-instantiation (`change-view-instantiation` work item)
- pytest-side equivalent of `--exclude-tag` (deferred to `pytest-plugin` work item — Django's `tag()` doesn't automatically become a pytest marker)
- Support for non-default `AUTH_USER_MODEL` beyond the `user_factory` escape hatch (no auto-detection of required fields)

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Which `AdminSite` to test | Class attribute `admin_site = django.contrib.admin.site`, override via subclassing | Satisfies "don't hardcode a single AdminSite" — the default is overridable, not baked in; matches system-architecture.md's stated usage pattern (host projects subclass the shipped `TestCase`) |
| URL resolution | `reverse(f"{admin_site.name}:{app_label}_{model_name}_{view}")`, never hardcoded patterns | Survives custom `AdminSite` instances with non-default `name`/namespace |
| Allowed status configurability | `allowed_status_codes = {200}` (class default) + `model_allowed_status_codes: dict[Model, set[int]]` per-model override | Directly validated by `testapp.RestrictedItem`, whose admin always returns 403 — dogfood subclass sets `model_allowed_status_codes = {RestrictedItem: {403}}` |
| Auth fixture creation | `user_factory: Callable[[], AbstractBaseUser] \| None = None` class attribute; falls back to a default `create_superuser(...)` call if unset | Mirrors the upcoming per-model `register_factory` concept, correctly scoped (one fixture here, not a registry) — unblocks custom `AUTH_USER_MODEL` projects without overengineering |
| Exclusion mechanism | `@tag("django_admin_tests")` (from `django.test`) on the class | Pure Django, not pytest — safe for `testcases.py`; enables `manage.py test --exclude-tag=django_admin_tests`. pytest-side equivalent deferred to `pytest-plugin` work item |
| Per-admin isolation | `self.subTest(model=model)` around each assertion | Matches `coding-standards.md`'s documented pattern — one failing admin doesn't hide others |

## Technical Approach

### Architecture

```
AdminSmokeTestCase(TestCase)                       [@tag("django_admin_tests")]
 ├─ admin_site: AdminSite                          (class attr, default django.contrib.admin.site)
 ├─ allowed_status_codes: set[int]                  (class attr, default {200})
 ├─ model_allowed_status_codes: dict[type, set[int]] (class attr, default {})
 ├─ user_factory: Callable[[], AbstractBaseUser] | None  (class attr, default None)
 ├─ setUpTestData()  → user_factory() if set, else default create_superuser(...)
 ├─ setUp()          → client.force_login(the user)
 ├─ _reverse_admin_url(model, view_name)      → reverse via admin_site.name namespace
 ├─ _assert_allowed_status(model, view_name, response)  → subTest + named failure message
 ├─ test_admin_smoke_changelist_returns_200() → iterates registry, subTest per model
 └─ test_admin_smoke_add_view_returns_200()   → same, for add views

tests/test_admin_smoke.py
 └─ AdminSmokeTest(AdminSmokeTestCase)
     model_allowed_status_codes = {RestrictedItem: {403}}
     + negative-path test (temporarily breaks CategoryAdmin.get_queryset,
       drives AdminSmokeTestCase manually via setUpClass/run(TestResult())/
       tearDownClass, asserts failure detected, restores in finally)
```

## Affected Files

| File | Action | Purpose |
|------|--------|---------|
| `django_admin_tests/testcases.py` | Modify | Implement `AdminSmokeTestCase` (currently a docstring-only stub) |
| `tests/test_admin_smoke.py` | Create | Dogfood tests: positive path via `testapp`, negative-path failure-detection test |

## Security Considerations

- **Disposable test superuser**: created only inside the test DB transaction, rolled back after each test; never touches real credentials. Password is a fixed test-only string, matching the pattern already accepted for `tests/settings.py`'s `SECRET_KEY`.
- **`RestrictedItem` fixture proves permission checks are respected**: the smoke test itself asserts a 403 for a permission-denied admin rather than silently passing, confirming the library doesn't accidentally bypass Django's permission system.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Custom `AUTH_USER_MODEL` with non-standard required fields breaks the default superuser creation | Medium | `user_factory` escape hatch; documented limitation for v0.1; not exercised by `testapp` (uses default `User`) |
| Proving negative-path failure detection requires manually driving `TestCase` lifecycle (`setUpClass`/`run(TestResult())`/`tearDownClass`) rather than a normal test invocation | Low (test-only, not shipped code) | Wrapped in `try/finally` to guarantee restoration even if the assertion itself fails; isolated to one test function in `tests/`; documented inline since it's non-obvious |
| Large admin registries could slow the host project's suite | Low | Per-admin overhead is one `GET` request each; NFR in system-architecture.md targets well under a second per admin |
| pytest users have no built-in equivalent to `--exclude-tag` | Low | Explicitly out of scope here; flagged for the `pytest-plugin` work item |

## Implementation Checklist

- [ ] `AdminSmokeTestCase` class attrs: `admin_site`, `allowed_status_codes`, `model_allowed_status_codes`, `user_factory`
- [ ] `@tag("django_admin_tests")` on the class
- [ ] `setUpTestData` (uses `user_factory` if set, else default superuser) + `setUp` (client login)
- [ ] `_reverse_admin_url` helper (namespace via `admin_site.name`)
- [ ] `_assert_allowed_status` helper (per-model override lookup, `subTest`, named failure message)
- [ ] `test_admin_smoke_changelist_returns_200`
- [ ] `test_admin_smoke_add_view_returns_200`
- [ ] Docstrings on class + public methods/attributes per coding-standards.md
- [ ] `tests/test_admin_smoke.py`: dogfood subclass against `testapp`, `model_allowed_status_codes = {RestrictedItem: {403}}`
- [ ] Negative-path test: temporarily break `CategoryAdmin.get_queryset`, drive `AdminSmokeTestCase` manually, assert failure detected, restore in `finally`
- [ ] Verify passes under both `pytest` and `manage.py test`; verify `--exclude-tag=django_admin_tests` actually excludes it

---
*Generated by specs.md - fabriqa.ai FIRE Flow | Checkpoint 1 approved: 2026-08-06T21:05:59Z*
