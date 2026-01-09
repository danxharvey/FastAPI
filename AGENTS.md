# Project Instructions

## Primary documentation sources
- For python use: https://docs.python.org/3/
- For streamlit use: https://docs.streamlit.io/
- For sqlite use: https://www.sqlite.org/docs.html
- For fastapi use: https://fastapi.tiangolo.com/
- For jwt use: https://jwt.io/introduction/


## Modular & Reusable Code
- Always set temperature = 0 for code execution workflows to ensure deterministic behavior.
- All new components should be modular and decoupled, minimizing dependencies.
- Functions and methods should perform a single, well-defined task.
- Classes should encapsulate related functionality with clear interfaces.
- Favor composition over inheritance to maximize flexibility and reusability.
- Ensure all new code is testable in isolation, including edge cases.
- Design code so it can be copied or reused in other projects without major changes.
- Always add comments to explain what you are doing.
- Add comprehensive logging and use the /logging folder (create as required).
- Adhere to Pythonic conventions for naming, readability, and maintainability.
- Before creating new functions or classes, check `utilities` or shared modules for existing reusable code.
- Before modifying any file:
    - Read the full file contents.
    - Identify all dependent modules, functions, and consumers.
- Apply the Read-Write-Reread protocol:
    - Reread every modified file after changes to ensure nothing is broken.
    - Beware of flake8, isort, mypy and black checks for code quality.
- When moving or refactoring code:
    - Update all references across the project.
    - Ensure dependencies are intact and no module relies on unstated assumptions.
- Edge-case testing is mandatory for all critical modules (auth, DB, shared modules, utilities).
- Load historical retro files (`.cursor/retro/retro_*`) before doctrine updates to prevent repeating past mistakes.


## Safe Decision-Making
- Always prioritize correctness and safety over speed or completion.
- If the agent is unsure of the correct action, or if an operation fails to pass tests after **3 consecutive attempts**, it must **stop and seek clarification from the user before proceeding**.
- All code modifications must pass all relevant unit and integration tests, including edge cases.
- Maintain temperature = 0 for execution workflows to ensure deterministic results.
- Do not proceed with any action that could break dependencies, introduce unstated assumptions, or violate critical module rules.