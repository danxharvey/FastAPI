# Retro Protocol Starter

## Phase 0: Session Analysis
- Review every turn of the conversation/session
- Produce key behavioral insights:
    - Successes
    - Failures
    - Actionable lessons

## Phase 0b: Load Historical Context
- Before distilling lessons, read all past retro files in `.cursor/retro/retro_*` (ignore the current session)
- Use insights from historical sessions to:
    - Detect repeated failure patterns
    - Confirm that lessons are truly durable
    - Avoid redundant or conflicting rule updates

## Phase 1: Lesson Distillation
- Abstract durable principles from current and historical sessions
- Categorize as:
    - **Global Doctrine** → universal, reusable principles
    - **Project Doctrine** → specific to this project’s tech, architecture, or workflow

## Phase 2: Doctrine Integration
- Integrate distilled lessons (from the current session and historical retros) into the appropriate `.cursor/rules/` file
- Refine existing rules if needed, or append new ones
- Ensure new or updated rules do not conflict with prior durable lessons
- Follow formatting and style conventions in the doctrine files

## Phase 3: Final Report
- List doctrine updates and changes (diffs if possible)
- Include session learnings for context
- Save session to `.cursor/retro/retro_<yyyymmmdd>.md` where `<yyyymmmdd>` is the current date (e.g., 2026Jan08)
