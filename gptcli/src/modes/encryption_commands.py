"""Logic for encrypt, decrypt, and rekey operations on stored data."""

import logging
import os
from collections.abc import Callable
from logging import Logger

from gptcli.src.common.api import SpinnerProgress
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.key_management import KeyManager, make_key_manager
from gptcli.src.common.passphrase import PassphrasePrompt

logger: Logger = logging.getLogger(__name__)

_SKIP_FILES: set[str] = {".install_successful"}


class EncryptionCommands:
    """Handles encrypt, decrypt, and rekey operations for provider storage.

    Attributes:
        _provider_dir: The root directory for the provider's data.
        _encryption: The Encryption instance to use for operations.
    """

    def __init__(self, provider_dir: str, encryption: Encryption) -> None:
        """Initialize with a provider directory and encryption instance.

        Args:
            provider_dir (str): The root directory for the provider (e.g., ~/.gptcli/mistral).
            encryption (Encryption): The Encryption instance to use.
        """
        self._provider_dir: str = provider_dir
        self._encryption: Encryption = encryption

    def _collect_files(self, include: Callable[[str], bool], skip_log: str) -> list[str]:
        """Collect file paths matching a predicate, skipping install markers.

        Args:
            include (Callable[[str], bool]): Predicate returning True for files to include.
            skip_log (str): Log message prefix for skipped files.

        Returns:
            list[str]: List of absolute paths to matching files.
        """
        files: list[str] = []
        for dirpath, _, filenames in os.walk(self._provider_dir):
            for filename in filenames:
                if filename in _SKIP_FILES:
                    continue
                if include(filename):
                    files.append(os.path.join(dirpath, filename))
                else:
                    logger.info(f"{skip_log}: {filename}")
        return files

    def _collect_encryptable_files(self) -> list[str]:
        """Collect all file paths eligible for encryption.

        Returns:
            list[str]: List of absolute paths to cleartext files.
        """
        return self._collect_files(
            include=lambda f: not f.endswith(".enc"),
            skip_log="Skipping already-encrypted file",
        )

    def _collect_decryptable_files(self) -> list[str]:
        """Collect all .enc file paths eligible for decryption.

        Returns:
            list[str]: List of absolute paths to .enc files.
        """
        return self._collect_files(
            include=lambda f: f.endswith(".enc"),
            skip_log="Skipping non-encrypted file",
        )

    def encrypt_provider(self) -> None:
        """Encrypt all cleartext files for the provider.

        Collects eligible files and encrypts any file that does not
        already have an .enc extension. Skips install marker files.
        """
        files: list[str] = self._collect_encryptable_files()
        with SpinnerProgress(total=len(files), label="Encrypting") as spinner:
            for filepath in files:
                self._encryption.encrypt_file(filepath)
                logger.info(f"Encrypted: {filepath}")
                spinner.advance()

    def decrypt_provider(self) -> None:
        """Decrypt all .enc files for the provider.

        Collects .enc files and decrypts each one, writing the cleartext
        to the original filename and removing the .enc file. Errors on
        individual files are logged but do not abort the batch.
        """
        files: list[str] = self._collect_decryptable_files()
        failed: list[str] = []
        with SpinnerProgress(total=len(files), label="Decrypting") as spinner:
            for enc_filepath in files:
                try:
                    plaintext: bytes | None = self._encryption.decrypt_file(enc_filepath)
                    if plaintext is None:
                        logger.error(f"Failed to decrypt: {enc_filepath}")
                        failed.append(enc_filepath)
                        spinner.advance()
                        continue
                    cleartext_filepath: str = enc_filepath[: -len(".enc")]
                    tmp_filepath: str = cleartext_filepath + ".tmp"
                    with open(tmp_filepath, "wb") as fp:
                        fp.write(plaintext)
                        fp.flush()
                        os.fsync(fp.fileno())
                    os.rename(tmp_filepath, cleartext_filepath)
                    os.remove(enc_filepath)
                    logger.info(f"Decrypted: {cleartext_filepath}")
                except Exception:
                    logger.exception(f"Failed to decrypt: {enc_filepath}")
                    failed.append(enc_filepath)
                spinner.advance()
        if failed:
            print(f"Warning: {len(failed)} file(s) failed to decrypt. Check logs for details.")

    @staticmethod
    def _collect_enc_files(providers: list[str]) -> list[str]:
        """Collect all .enc file paths across provider directories.

        Args:
            providers (list[str]): List of provider directory paths.

        Returns:
            list[str]: List of absolute paths to .enc files.
        """
        enc_files: list[str] = []
        for provider_dir in providers:
            for dirpath, _, filenames in os.walk(provider_dir):
                for filename in filenames:
                    if filename.endswith(".enc") and filename not in _SKIP_FILES:
                        enc_files.append(os.path.join(dirpath, filename))
        return enc_files

    @staticmethod
    def rekey(old_encryption: Encryption, providers: list[str]) -> bool:
        """Re-encrypt all files with a new passphrase using atomic operations.

        Three-phase approach for crash safety:
        1. Decrypt each .enc file with old key, re-encrypt with new key, write to .enc.new
        2. Swap: remove old .enc, rename .enc.new to .enc
        3. Delete old key material, write new salt/verify/key files

        On failure, cleans up all .enc.new files. Old .enc files remain valid.

        Args:
            old_encryption (Encryption): The Encryption instance with the old key.
            providers (list[str]): List of provider directory paths to rekey.

        Returns:
            bool: True if rekey succeeded, False if passphrase verification failed.
        """
        km: KeyManager = make_key_manager()

        old_passphrase: str | None = PassphrasePrompt.prompt("Enter current encryption passphrase: ")
        if old_passphrase is None:
            return False
        if not km.verify_passphrase(old_passphrase):
            print("Incorrect passphrase.")
            return False

        new_passphrase: str | None = PassphrasePrompt.create_with_confirmation(
            prompt="Enter new encryption passphrase: "
        )
        if new_passphrase is None:
            return False
        new_salt: bytes = Encryption.generate_salt()
        new_key: bytes = Encryption.derive_key(new_passphrase, new_salt)
        new_encryption = Encryption(key=new_key)

        enc_files: list[str] = EncryptionCommands._collect_enc_files(providers)
        new_files: list[str] = []

        try:
            # Phase 1: Decrypt with old key, re-encrypt with new key, write to .enc.new
            for enc_filepath in enc_files:
                plaintext: bytes | None = old_encryption.decrypt_file(enc_filepath)
                if plaintext is None:
                    raise RuntimeError(f"Failed to decrypt file during rekey: {enc_filepath}")
                encrypted: bytes = new_encryption.encrypt(plaintext)
                new_filepath: str = enc_filepath + ".new"
                with open(new_filepath, "wb") as fp:
                    fp.write(encrypted)
                new_files.append(new_filepath)
                logger.info(f"Re-encrypted to temp file: {new_filepath}")

            # Phase 2: Atomically swap .enc.new -> .enc (os.rename replaces on POSIX)
            for enc_filepath in enc_files:
                new_filepath = enc_filepath + ".new"
                os.rename(new_filepath, enc_filepath)
                logger.info(f"Swapped: {enc_filepath}")

        except Exception:
            # Clean up .enc.new files on failure
            for new_filepath in new_files:
                if os.path.exists(new_filepath):
                    os.remove(new_filepath)
            raise

        # Phase 3: Update key material
        km.replace_key_material(salt=new_salt, key=new_key)
        return True
