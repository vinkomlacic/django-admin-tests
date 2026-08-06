---
id: ci-matrix
title: GitHub Actions CI matrix
intent: core-package
complexity: medium
mode: confirm
status: pending
depends_on: [dev-testapp, admin-smoke-testcase-core, change-view-instantiation, pytest-plugin]
created: 2026-08-06T20:27:17Z
---

# Work Item: GitHub Actions CI matrix

## Description

Add GitHub Actions CI running this repo's own test suite (testapp dogfood
tests) across a matrix of supported Python versions, supported Django
versions, and both test runners (`manage.py test` and pytest), per
tech-stack.md's CI conventions.

## Acceptance Criteria

- [ ] Workflow matrix covers Python 3.10-3.12 x Django 4.2/5.x (current LTS + latest) x runner (native, pytest)
- [ ] Each matrix cell installs the package (editable) plus dev deps and runs testapp's dogfood tests via the appropriate runner
- [ ] CI fails loudly if either runner regresses independently (runner failures aren't masked by matrix continue-on-error)
- [ ] Workflow triggers on push and pull_request
- [ ] All matrix cells pass on the current codebase

## Technical Notes

(none)

## Dependencies

- dev-testapp
- admin-smoke-testcase-core
- change-view-instantiation
- pytest-plugin
