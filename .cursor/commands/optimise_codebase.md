# Refactor Code Task

## Phase 0: Reconnaissance
- Read the entire codebase, including current modules, `utilities` and critical zones.
- Identify duplicated or reusable functionality.
- Produce a concise summary of potential refactor targets.

## Phase 1: Planning
- Decide which functions, classes, or modules can be moved to `utilities` or refactored.
- Prioritize high-impact changes first (core modules, auth, DB, shared logic).
- Confirm and write tests and edge-case coverage required.

## Phase 2: Execution
- Follow Read-Write-Reread for all file modifications.
- Move reusable functions to `utilities` or shared modules, updating all dependencies.
- Update all references and dependencies across the project.
- Maintain modular design and adherence to OOP best practices.
- Run unit/integration tests after each significant change.
- If tests fail 3 times, halt workflow and request clarification.

## Phase 3: Verification
- Ensure all tests pass.
- Verify system-wide consistency and no regressions.
- Produce a summary of changes with updated locations, diffs, and new test coverage.

## Phase 4: Reporting
- Document all refactorings in a concise report.
- Highlight new reusable components in `utilities`.
- Suggest any remaining refactor opportunities for future sessions.
