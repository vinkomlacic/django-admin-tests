---
id: package-skeleton
title: Package skeleton and build config
intent: core-package
complexity: low
mode: autopilot
status: completed
depends_on: []
created: 2026-08-06T20:27:17Z
run_id: run-django-admin-tests-001
completed_at: 2026-08-06T20:36:21.169Z
---

# Work Item: Package skeleton and build config

## Description

Set up the installable package skeleton for django-admin-tests: pyproject.toml
(hatchling build backend, project metadata, Django>=4.2 as the only prod
dependency), the `django_admin_tests/` package directory with `__init__.py`
and stub `testcases.py` / `pytest_plugin.py` modules, and ruff lint/format
config. This is the foundation every other work item builds on.

## Acceptance Criteria

- [ ] pyproject.toml declares project metadata, Django>=4.2 as the only prod dependency, and hatchling as build backend
- [ ] `django_admin_tests/` package exists with `__init__.py`, `testcases.py` (stub), `pytest_plugin.py` (stub)
- [ ] ruff configured in pyproject.toml for linting and formatting per coding-standards.md
- [ ] `pip install -e .` succeeds locally
- [ ] Repo layout matches file layout conventions in coding-standards.md

## Technical Notes

`testcases.py` must never import pytest (see CLAUDE.md / system-architecture.md).
Keep stubs minimal — real implementation lands in later work items.

## Dependencies

(none)
