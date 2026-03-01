"""Logic for nuking all gptcli data."""

import os
import shutil


class Nuke:
    """Handles permanent deletion of all gptcli data."""

    @staticmethod
    def nuke(root_dir: str) -> bool:
        """Permanently delete the entire gptcli data directory.

        Args:
            root_dir (str): The root directory to delete (e.g., ~/.gptcli).

        Returns:
            bool: True if the directory was deleted, False if the user aborted or the directory does not exist.
        """
        if not os.path.isdir(root_dir):
            print(f"Directory does not exist: {root_dir}")
            return False

        print(f"WARNING: This will permanently delete all gptcli data in: {root_dir}")
        print("This includes chat history, API keys, encryption key material, and OCR results.")
        print("This action is irreversible.")
        try:
            confirmation: str = input('\nType "yes" to confirm: ')
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            return False

        if confirmation != "yes":
            print("Aborted.")
            return False

        try:
            shutil.rmtree(root_dir)
        except FileNotFoundError:
            print(f"Directory does not exist: {root_dir}")
            return False
        except OSError as exc:
            print(f"Failed to delete {root_dir}: {exc}")
            return False
        print(f"Deleted: {root_dir}")
        return True
