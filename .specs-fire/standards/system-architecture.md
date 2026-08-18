# System Architecture

## Overview

`django-admin-tests` is a pip-installable Django app. A host project installs it, adds it to `INSTALLED_APPS`, and wires in its `TestCase` (directly or via an optional pytest plugin). From then on, whenever the host project runs *its own* test command — `manage.py test` or `pytest` — every registered `ModelAdmin` in that project gets smoke-tested automatically (changelist/add/change views return 200, or another allowed status).

## System Context

The host project owns the test run; this library only supplies test code and discovery hooks that plug into it. There is no server, API, or deployment for this library itself — it ships as a package and runs entirely inside the host project's test process.

### Context Diagram

```
┌────────────────────┐
│   Host project     │
│  (installs pkg,    │
│  runs its own      │
│  test command)     │
└─────────┬──────────┘
          │ manage.py test  OR  pytest
          ▼
┌───────────────────────────────────────────┐
│  django-admin-tests (installed package)     │
│                                             │
│  ┌────────────────────┐  ┌────────────────┐ │
│  │ AdminSmokeTestCase │  │ pytest plugin  │ │
│  │ (unittest-based,   │  │ (optional,     │ │
│  │  runner-agnostic)  │  │  pytest11)     │ │
│  └─────────┬──────────┘  └───────┬────────┘ │
└────────────┼─────────────────────┼──────────┘
             │ iterates            │ auto-registers
             ▼                     ▼
      django.contrib.admin.site._registry
             │
             ▼
      Host project's models / DB
```

### Users

- **Host project developer**: installs the package, adds a one-line import (or relies on the pytest plugin), runs their existing test command.
- **CI system (host project's)**: runs the host project's test suite, which now includes admin smoke coverage.

### External Systems

None — this library never runs standalone; it always executes inside a host Django project's process.

## Architecture Pattern

**Pattern**: Distributable Django app ("pluggable app") exposing a runner-agnostic `TestCase`, with an optional pytest plugin layered on top for zero-config discovery.
**Rationale**: `unittest.TestCase` is the lowest common denominator both Django's native runner and pytest can discover; the pytest plugin is additive convenience, never a requirement.

## Component Architecture

### Components

#### Core library (`django_admin_tests/testcases.py`)

- **Purpose**: Provide `AdminSmokeTestCase`, a Django `TestCase` subclass that generates one test method per (registered `ModelAdmin`, view) and asserts each view responds successfully.
- **Responsibilities**: Admin registry introspection and method generation (at class-creation time, via the `AdminSmokeMeta` metaclass), view URL resolution, request issuing via the Django test client, assertions. Exclusions are resolved per run inside each generated method, not at generation time, so settings overrides still apply.
- **Dependencies**: Django only (no pytest dependency at this layer).

#### pytest plugin (`django_admin_tests/pytest_plugin.py`, optional)

- **Purpose**: Auto-discover and register the smoke tests under pytest without requiring the host project to write an import.
- **Responsibilities**: Registered via the `pytest11` entry point; hooks into pytest collection to surface the `TestCase`-based tests.
- **Dependencies**: pytest (only pulled in if the host project has pytest installed; never required for the `manage.py test` path).

#### Internal `testapp` (dev-only, not shipped)

- **Purpose**: Give this repository's own CI something to run `AdminSmokeTestCase` against, so the library is tested against real `ModelAdmin`s under both runners.
- **Responsibilities**: Sample models/admin registrations used only in this repo's own test matrix.
- **Dependencies**: Django, this library's own test suite (pytest-django in dev).

### Component Diagram

```
host project ──installs──▶ django_admin_tests (core library)
                                   ▲
                                   │ optional
                          pytest_plugin.py

this repo's CI ──uses──▶ testapp/ ──exercised by──▶ core library (dogfooding)
```

## Data Flow

1. Host project runs `manage.py test` or `pytest`.
2. Importing the test module creates `AdminSmokeTestCase` (or a subclass), and the metaclass binds one test method per (registered `ModelAdmin`, view).
3. The runner discovers those methods (via explicit import, or via the pytest plugin under pytest). Each resolves its model's changelist/add/change URL and issues a request through the Django test client against the host project's own DB.
4. Assertions on response status surface as normal test failures in the host project's existing test output.

```
manage.py test / pytest ─▶ AdminSmokeTestCase ─▶ admin.site._registry ─▶ Django test client ─▶ host project DB
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Test authoring | Django `TestCase` (unittest) | Runner-agnostic tests shipped to consumers |
| Native runner support | `manage.py test` | Works via one-line import, zero extra dependency |
| pytest support | pytest-django (consumer) + optional `pytest11` plugin (this package) | One-line import always works; plugin adds auto-discovery |
| Data | SQLite (this repo's own dev/CI); host project's DB in real usage | Fast local iteration on this library |
| CI | GitHub Actions | Matrix over Python × Django × runner (native/pytest) |
| Packaging | pyproject.toml + hatchling + hatch-vcs | PyPI distribution, entry-point declaration, git-tag-derived version |

## Non-Functional Requirements

### Performance

- **Per-admin overhead**: smoke-testing one `ModelAdmin` should add well under a second to the host project's suite, so it scales to projects with dozens of registered admins.

### Security

- No real credentials in this repo's own fixtures; host projects supply their own test users/permissions.
- The library must not require elevated DB access beyond what the host project's test settings already grant.

### Scalability

Designed to run against admin registries of any size; consumers can opt individual `ModelAdmin`s out if a given view is expensive or intentionally non-200 (e.g., custom permission-denied flows).

## Constraints

- No network calls; everything runs against the host project's local test DB.
- Must not require pytest to be installed for the core (`manage.py test`) path.
- Must not assume a specific host project structure beyond having `django.contrib.admin` configured.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Test authoring style | `unittest`-based Django `TestCase`, not pytest-native | Only format discoverable by both `manage.py test` and pytest |
| Distribution model | Installable Django app (pip package) + optional pytest plugin | One-line import always works; plugin is additive convenience for pytest users, not a hard requirement |
| Internal dev/test tooling | pytest-django (used only to test this library itself) | Convenient for this repo's own CI; irrelevant to how consumers run their tests |

---
*Generated by specs.md - fabriqa.ai FIRE Flow*
