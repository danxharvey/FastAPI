# Code Workflow Template

## Phase 0: Reconnaissance
- Scan the project repo, read all files relevant to the requested task.
- Produce a concise digest (≤200 lines) summarizing architecture, dependencies, and patterns.

## Phase 1: Planning
- Restate the task clearly.
- Identify all impacted modules and components.
- Justify the chosen approach in alignment with project doctrine.
- Confirm and write tests and edge-case coverage required.

## Phase 2: Execution
- Follow Read-Write-Reread for all file modifications.
- Read each file immediately before and after modification.
- **Clarification Threshold:** If unsure after 3 attempts, stop and ask the user for guidance.
- Apply Safe Decision-Making rules.

## Phase 3: Verification
- Run all relevant unit and integration tests, including edge cases.
- If a test fails, diagnose and fix before proceeding.
- Ensure system-wide consistency.
- Verify that no unstated assumptions were introduced in any module.