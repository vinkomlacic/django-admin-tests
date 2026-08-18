---
id: docs-and-changelog
title: Update docs and changelog for the new method names
intent: per-model-test-methods
complexity: low
mode: autopilot
status: completed
depends_on:
  - generated-test-methods
created: 2026-08-18T20:12:19Z
run_id: run-django-admin-tests-008
completed_at: 2026-08-18T20:40:53.069Z
---

# Work Item: Update docs and changelog for the new method names

## Description

Documentation fallout from removing the three aggregate test methods. The old
names appear in user-facing docs and in this project's own standards files, and
the removal is a breaking change that needs a migration note per the
constitution ("Breaking changes require migration notes").

## Acceptance Criteria

- [ ] `CHANGELOG.md` `[Unreleased]` documents the removal of `test_admin_smoke_changelist_returns_200`, `test_admin_smoke_add_view_returns_200` and `test_admin_smoke_change_view_returns_200` under `### Changed` (or `### Removed`), with the new naming scheme and a note for anyone selecting the old node IDs in CI config
- [ ] `README.md` reflects per-model tests: usage section, the "Turning it off" section if it references specific names, and "Known limitations"
- [ ] README documents that the tests are now individually selectable (e.g. `pytest -k testapp_product`) — one of the motivating benefits
- [ ] README no longer promises "200" where the method name previously implied it, since allowed status codes are configurable
- [ ] `.specs-fire/standards/coding-standards.md:39` example updated (currently `test_admin_smoke_changelist_returns_200`)
- [ ] `.specs-fire/standards/testing-standards.md:42` example updated, and the illustrative `AdminSmokeTestCase` code block at lines 48-64 no longer shows the registry-looping style
- [ ] `.specs-fire/standards/system-architecture.md` updated if it describes the looping approach
- [ ] No stale references to the three old names remain outside `.specs-fire/runs/` (historical run logs stay untouched)

## Technical Notes

**Changelog scope check.** Per constitution.md, changelog entries cover only
user-visible changes. This one qualifies squarely — it's a breaking change to
the public API's test method names.

**Leave run logs alone.** `.specs-fire/runs/**` and the completed
`core-package` work items are historical records of what was built at the time;
they should keep referencing the old names. Only live docs and standards get
updated.

**Standards files are self-referential here.** `testing-standards.md` uses the
old names as its canonical naming-pattern example, and its "Test Structure"
section shows a `for model in admin.site._registry` loop as the shipped-code
example. Both now describe an approach the codebase no longer uses.

## Dependencies

- generated-test-methods
