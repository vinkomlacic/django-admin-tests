# django-admin-tests

A pip-installable Django app that gives host projects automatic admin smoke-test
coverage: every registered `ModelAdmin`'s changelist/add/change views are asserted
to return 200 as part of the *host project's own* test run — under either Django's
native `manage.py test` or pytest.

## Before making changes

This project uses FIRE (Fast Intent-Run Engineering) for planning and execution.
Read these before writing code:

- `.specs-fire/standards/constitution.md` — git workflow, commit granularity, review/CI policy
- `.specs-fire/standards/tech-stack.md` — languages, frameworks, dependencies
- `.specs-fire/standards/coding-standards.md` — file layout, naming, import order
- `.specs-fire/standards/testing-standards.md` — test conventions (note: shipped code and this repo's own tests follow different rules — see the file)
- `.specs-fire/standards/system-architecture.md` — components and how they fit together
- `.specs-fire/state.yaml` — current intents/work items/run status

## The one rule most likely to be missed

Code shipped under `django_admin_tests/testcases.py` must **never** import pytest.
It has to run under both `manage.py test` and pytest, and pytest-native code breaks
the former entirely. Pytest-specific glue belongs only in
`django_admin_tests/pytest_plugin.py`. See `system-architecture.md` for why.

## Git workflow

One commit per completed work item (see constitution.md for full policy) — don't
bundle multiple work items into a single commit. Update `CHANGELOG.md` under
`[Unreleased]` in that same commit for any user-facing change.

## Working via FIRE

Run `/specsmd-fire` to route to the right agent (Planner for new intents/work
items, Builder for executing them).
