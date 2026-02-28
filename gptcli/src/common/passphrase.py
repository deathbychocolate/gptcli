"""Handles passphrase confirmation."""

import getpass
import logging
from logging import Logger

_MAX_RETRIES: int = 3
_MIN_LENGTH: int = 16


logger: Logger = logging.getLogger(__name__)


class PassphrasePrompt:
    """Handles passphrase creation with confirmation."""

    @staticmethod
    def prompt(message: str) -> str | None:
        """Prompt for input via getpass, returning None on abort.

        Handles KeyboardInterrupt (Ctrl+C) and EOFError (Ctrl+D) by
        printing a message and returning None.

        Args:
            message (str): The prompt message to display.

        Returns:
            str | None: The entered text, or None if the user aborted.
        """
        try:
            return getpass.getpass(message)
        except KeyboardInterrupt:
            logger.warning("Detected 'KeyboardInterrupt', aborting passphrase prompt.")
            print("Aborting passphrase prompt.")
            return None
        except EOFError:
            logger.warning("Detected 'EOFError', aborting passphrase prompt.")
            print("Aborting passphrase prompt.")
            return None
        except Exception:
            logger.warning("Detected 'Exception', aborting passphrase prompt.")
            print("Aborting passphrase prompt. Reason: Unknown Exception.")
            return None

    @staticmethod
    def create_with_confirmation(prompt: str = "Create an encryption passphrase: ") -> str | None:
        """Prompt for a passphrase and confirm, retrying on mismatch.

        Allows up to _MAX_RETRIES attempts for the user to enter matching
        passphrases before returning None. The passphrase must be at least
        _MIN_LENGTH characters long.

        Args:
            prompt (str): The prompt message for passphrase entry.

        Returns:
            str | None: The confirmed passphrase, or None if the user aborted
                or exceeded the maximum number of retries.
        """
        for _ in range(_MAX_RETRIES):
            passphrase: str | None = PassphrasePrompt._prompt_for_valid_passphrase(prompt)
            if passphrase is None:
                return None
            confirmation: str | None = PassphrasePrompt.prompt("Confirm encryption passphrase: ")
            if confirmation is None:
                return None
            if passphrase == confirmation:
                return passphrase
            print("Passphrases do not match. Please try again.")
        return None

    @staticmethod
    def _prompt_for_valid_passphrase(prompt: str) -> str | None:
        """Prompt repeatedly until the passphrase meets the minimum length.

        Args:
            prompt (str): The prompt message for passphrase entry.

        Returns:
            str | None: A passphrase that meets the minimum length requirement,
                or None if the user aborted.
        """
        while True:
            passphrase: str | None = PassphrasePrompt.prompt(prompt)
            if passphrase is None:
                return None
            if len(passphrase) >= _MIN_LENGTH:
                return passphrase
            print(f"Passphrase must be at least {_MIN_LENGTH} characters. Please try again.")
