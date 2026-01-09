#!/usr/bin/env python3
"""
Local pre-commit / mini-CI script.

Runs:
1. Code formatting checks (Black + isort)
2. Linting (flake8)
3. Type checking (mypy) across entire project
4. Tests + coverage (pytest)
Excludes common unwanted directories like .venv, __pycache__, node_modules.
"""

import subprocess
import sys

EXCLUDE = ".venv"


def run_cmd(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n=== {description} ===")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"{description}: ✅ Passed")
        return True
    except subprocess.CalledProcessError:
        print(f"{description}: ❌ Failed")
        return False


def main():
    all_passed = True

    # 1. Formatting checks exclude .venv, __pycache__, node_modules using regex
    all_passed &= run_cmd(
        r"black . --exclude '(\.venv|__pycache__|node_modules)'",
        "Black formatting check",
    )
    all_passed &= run_cmd(
        "isort --profile black . --skip .venv --skip __pycache__ --skip node_modules",
        "isort import check",
    )

    # 2. Linting
    all_passed &= run_cmd(
        f"flake8 . --max-line-length=88 --exclude={EXCLUDE}", "flake8 linting"
    )

    # 3. Type checking
    all_passed &= run_cmd(
        f"mypy . --ignore-missing-imports --explicit-package-bases \
        --exclude '{EXCLUDE}'",
        "mypy type checking",
    )

    # 4. Run tests + coverage
    all_passed &= run_cmd(
        "python -m pytest --maxfail=1 --disable-warnings \
        --cov-report=term --ignore=.venv",
        "pytest + coverage",
    )

    if all_passed:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n⚠️ Some checks failed. Fix issues before commit/push.")
        sys.exit(1)


if __name__ == "__main__":
    main()
