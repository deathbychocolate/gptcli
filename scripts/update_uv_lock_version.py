#!/usr/bin/env python3
"""Update the project version in uv.lock after a commitizen bump.

This script reads the new version from pyproject.toml and updates
only the dbc-gptcli package version in uv.lock, leaving all other
package versions untouched.
"""

import subprocess
import tomllib
from pathlib import Path


def get_project_version() -> str:
    """Read the current version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    data = tomllib.loads(pyproject.read_text())
    version: str = data["project"]["version"]
    return version


def update_uv_lock_version(new_version: str) -> bool:
    """Update the dbc-gptcli version in uv.lock and stage the file.

    Args:
        new_version (str): The new version string to set.

    Returns:
        bool: True if the version was updated, False otherwise.
    """
    lock_file = Path("uv.lock")
    lines = lock_file.read_text().splitlines()

    found_package = False

    for i, line in enumerate(lines):
        if line == 'name = "dbc-gptcli"':
            found_package = True
            continue

        if found_package and line.startswith("version = "):
            lines[i] = f'version = "{new_version}"'
            lock_file.write_text("\n".join(lines) + "\n")
            subprocess.run(["git", "add", "uv.lock"], check=True)
            return True

    return False


def main() -> None:
    version = get_project_version()
    if update_uv_lock_version(version):
        print(f"Updated uv.lock to version {version}")
    else:
        print("WARNING: Could not find dbc-gptcli package in uv.lock")
        print("WARNING: Proceeding without version bump in uv.lock")


if __name__ == "__main__":
    main()
