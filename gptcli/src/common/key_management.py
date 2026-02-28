"""Handles encryption key lifecycle: salt, key cache, and verification token."""

import contextlib
import json
import logging
import math
import os
import stat
import struct
import sys
import tempfile
import time
from collections.abc import Generator
from logging import Logger

from gptcli.src.common.encryption import (
    _SCRYPT_N,
    _SCRYPT_P,
    _SCRYPT_R,
    Encryption,
)
from gptcli.src.common.passphrase import PassphrasePrompt

logger: Logger = logging.getLogger(__name__)

_KEY_SESSION_DURATION: float = 43200.0  # 12 hours in seconds
_TIMESTAMP_SIZE: int = 8  # bytes for big-endian double
_KEY_SIZE: int = 32
_WRAPPING_KEY_SIZE: int = 32
_MAX_PASSPHRASE_ATTEMPTS: int = 3
_WRAPPING_KEY_FILENAME: str = (
    f"gptcli_wrapping_{os.getuid()}.key" if sys.platform == "linux" else "gptcli_wrapping.key"
)


def make_key_manager(no_cache: bool = False) -> "KeyManager":
    """Create a KeyManager with standard application paths.

    Args:
        no_cache (bool): If True, never read or write the key cache or wrapping key files.

    Returns:
        KeyManager: A KeyManager configured with the standard salt, key, verify, and params paths.
    """
    from gptcli.constants import (
        GPTCLI_KDF_PARAMS_FILE,
        GPTCLI_KEY_CACHE_FILE,
        GPTCLI_SALT_FILE,
        GPTCLI_VERIFY_FILE,
    )

    return KeyManager(
        salt_path=GPTCLI_SALT_FILE,
        key_path=GPTCLI_KEY_CACHE_FILE,
        verify_path=GPTCLI_VERIFY_FILE,
        params_path=GPTCLI_KDF_PARAMS_FILE,
        no_cache=no_cache,
    )


class KeyManager:
    """Manages the lifecycle of encryption keys for data at rest.

    Handles salt generation, key derivation, key caching with 12-hour
    expiry, and passphrase verification. The on-disk key cache is encrypted
    with an ephemeral wrapping key stored in volatile storage (tmpfs/ramfs),
    making it unreadable after reboot.

    Attributes:
        _salt_path: Path to the salt file.
        _key_path: Path to the cached key file (encrypted with wrapping key).
        _verify_path: Path to the verification token file.
        _params_path: Path to the KDF parameters file.
        _wrapping_key_path: Path to the wrapping key file in volatile storage.
    """

    def __init__(
        self,
        salt_path: str,
        key_path: str,
        verify_path: str,
        params_path: str | None = None,
        wrapping_key_path: str | None = None,
        no_cache: bool = False,
    ) -> None:
        """Initialize with paths to salt, key cache, verification, and KDF params files.

        Args:
            salt_path (str): Path to the salt file (.salt).
            key_path (str): Path to the cached key file (.key).
            verify_path (str): Path to the verification token file (.verify.enc).
            params_path (str | None): Path to the KDF parameters file (.kdf_params). Defaults to None.
            wrapping_key_path (str | None): Path to wrapping key file in volatile storage.
                If None, auto-detected via _get_volatile_dir(). Allows tests to use tmp_path.
            no_cache (bool): If True, never read or write the key cache or wrapping key files.
        """
        self._salt_path: str = salt_path
        self._key_path: str = key_path
        self._verify_path: str = verify_path
        self._params_path: str | None = params_path
        self._no_cache: bool = no_cache
        if wrapping_key_path is not None:
            self._wrapping_key_path: str = wrapping_key_path
        else:
            self._wrapping_key_path = os.path.join(self._get_volatile_dir(), _WRAPPING_KEY_FILENAME)

    @staticmethod
    def _get_volatile_dir() -> str:
        """Return a directory backed by volatile storage (cleared on reboot).

        On Linux, uses /dev/shm if available (tmpfs), otherwise falls back to
        the system temp directory. On macOS, uses the per-user temp directory
        (under /var/folders), which is cleaned on reboot.

        Returns:
            str: Path to a volatile directory.
        """
        if sys.platform == "linux" and os.path.isdir("/dev/shm"):
            return "/dev/shm"
        return tempfile.gettempdir()

    @staticmethod
    def _write_restricted(filepath: str, data: bytes) -> None:
        """Write binary data to a file with owner-only permissions (0o600).

        Args:
            filepath (str): Path to the file to write.
            data (bytes): The binary data to write.
        """
        with open(filepath, "wb") as fp:
            fp.write(data)
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)

    @staticmethod
    @contextlib.contextmanager
    def _atomic_writes() -> Generator[list[str], None, None]:
        """Context manager that tracks written files and removes them on failure.

        Yields a list that callers append file paths to after each write.
        If an exception occurs, all tracked files are removed before re-raising.

        Yields:
            list[str]: A list to track written file paths.
        """
        written: list[str] = []
        try:
            yield written
        except Exception:
            for filepath in written:
                if os.path.exists(filepath):
                    os.remove(filepath)
            raise

    def _get_or_create_wrapping_key(self) -> bytes:
        """Read the wrapping key from volatile storage, or generate a new one.

        Uses O_CREAT | O_EXCL for atomic creation to prevent TOCTOU races.

        Returns:
            bytes: The 32-byte wrapping key.
        """
        try:
            fd: int = os.open(self._wrapping_key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            existing: bytes | None = self._read_wrapping_key()
            if existing is not None:
                return existing
            os.remove(self._wrapping_key_path)
            return self._get_or_create_wrapping_key()
        wrapping_key: bytes = os.urandom(_WRAPPING_KEY_SIZE)
        os.write(fd, wrapping_key)
        os.close(fd)
        return wrapping_key

    def _read_wrapping_key(self) -> bytes | None:
        """Read the wrapping key from volatile storage.

        Returns:
            bytes | None: The 32-byte wrapping key, or None if missing or invalid.
        """
        if not os.path.exists(self._wrapping_key_path):
            return None
        with open(self._wrapping_key_path, "rb") as fp:
            data: bytes = fp.read()
        if len(data) != _WRAPPING_KEY_SIZE:
            return None
        return data

    def is_initialized(self) -> bool:
        """Check if encryption has been initialized.

        Returns:
            bool: True if both salt and verification files exist.
        """
        return os.path.exists(self._salt_path) and os.path.exists(self._verify_path)

    def initialize(self, passphrase: str) -> bytes:
        """Perform first-time encryption setup.

        Generates a salt, derives a key from the passphrase, creates a
        verification token, and writes an encrypted timestamped key file.
        Cleans up partially written files on failure.

        Args:
            passphrase (str): The user's chosen passphrase.

        Returns:
            bytes: The 32-byte derived encryption key.

        Raises:
            RuntimeError: If encryption is already initialized.
        """
        if self.is_initialized():
            raise RuntimeError("Encryption is already initialized.")

        with self._atomic_writes() as written:
            salt: bytes = Encryption.generate_salt()
            self._write_restricted(self._salt_path, salt)
            written.append(self._salt_path)

            n: int = _SCRYPT_N
            key: bytes = Encryption.derive_key(passphrase, salt, n=n)

            token: bytes = Encryption.create_verification_token(key)
            self._write_restricted(self._verify_path, token)
            written.append(self._verify_path)

            if self._params_path is not None:
                params_json: bytes = json.dumps({"n": n, "r": _SCRYPT_R, "p": _SCRYPT_P}).encode("utf-8")
                self._write_restricted(self._params_path, params_json)
                written.append(self._params_path)

            if not self._no_cache:
                self._cache_key(key)
                written.append(self._key_path)

        return key

    def load_key(self) -> bytes | None:
        """Load the encryption key from cache or prompt for passphrase.

        If the wrapping key is missing (e.g. after reboot), the encrypted key
        cache is unreadable and is deleted. If the key cache exists and is not
        expired, decrypts and returns the key. Otherwise prompts for passphrase.

        Returns:
            bytes | None: The 32-byte encryption key, or None if all attempts failed.
        """
        cached: bytes | None = self._load_from_cache()
        if cached is not None:
            return cached
        return self._prompt_for_key()

    def _load_from_cache(self) -> bytes | None:
        """Attempt to load the encryption key from the on-disk cache.

        Handles missing wrapping keys (post-reboot), expired keys, and
        decryption failures by removing stale cache files.

        Returns:
            bytes | None: The cached key if valid and unexpired, None otherwise.
        """
        if self._no_cache or not os.path.exists(self._key_path):
            return None

        cached_data: tuple[float, bytes] | None = self._read_cached_key_data()
        if cached_data is None:
            return None

        timestamp, key_bytes = cached_data
        elapsed: float = time.time() - timestamp
        if elapsed > _KEY_SESSION_DURATION:
            logger.info("Key session expired, removing key file.")
            os.remove(self._key_path)
            return None

        logger.info("Loading encryption key from cache.")
        return key_bytes

    def _prompt_for_key(self) -> bytes | None:
        """Prompt the user for a passphrase and derive the encryption key.

        Allows up to _MAX_PASSPHRASE_ATTEMPTS before giving up.

        Returns:
            bytes | None: The derived key if passphrase is correct, None otherwise.
        """
        logger.info("Key cache not found, prompting for passphrase.")
        for attempt in range(_MAX_PASSPHRASE_ATTEMPTS):
            passphrase: str | None = PassphrasePrompt.prompt("Enter encryption passphrase: ")
            if passphrase is None:
                return None
            key: bytes | None = self._derive_and_verify(passphrase)
            if key is not None:
                if not self._no_cache:
                    self._cache_key(key)
                return key
            if attempt < _MAX_PASSPHRASE_ATTEMPTS - 1:
                print("Incorrect passphrase. Please try again.")
            else:
                print("Incorrect passphrase.")
        return None

    def _read_cached_key_data(self) -> tuple[float, bytes] | None:
        """Read and decrypt the cached key file, returning timestamp and key bytes.

        Handles missing wrapping keys and decryption failures by cleaning up
        stale cache files.

        Returns:
            tuple[float, bytes] | None: A (timestamp, key_bytes) tuple, or None if
                the cache is unreadable or invalid.
        """
        wrapping_key: bytes | None = self._read_wrapping_key()
        if wrapping_key is None:
            logger.info("Wrapping key missing (post-reboot), removing stale key cache.")
            os.remove(self._key_path)
            return None

        with open(self._key_path, "rb") as fp:
            encrypted_data: bytes = fp.read()
        plaintext: bytes | None = Encryption(wrapping_key).decrypt(encrypted_data)
        if plaintext is None:
            logger.warning("Failed to decrypt key cache; removing stale key cache.")
            os.remove(self._key_path)
            return None
        if len(plaintext) < _TIMESTAMP_SIZE + _KEY_SIZE:
            logger.warning("Cached key file has unexpected length; removing stale key cache.")
            os.remove(self._key_path)
            return None

        timestamp: float = struct.unpack(">d", plaintext[:_TIMESTAMP_SIZE])[0]
        if not math.isfinite(timestamp):
            logger.warning("Cached key file has invalid timestamp; removing stale key cache.")
            os.remove(self._key_path)
            return None

        key_bytes: bytes = plaintext[_TIMESTAMP_SIZE:]
        return (timestamp, key_bytes)

    def _cache_key(self, key: bytes) -> None:
        """Write an encrypted timestamped key file.

        Encrypts (8-byte timestamp + 32-byte key) with the wrapping key
        before writing to disk.

        Binary layout (plaintext before wrapping encryption):
            [8-byte big-endian IEEE-754 double timestamp][32-byte key]

        Args:
            key (bytes): The 32-byte encryption key to write.
        """
        wrapping_key: bytes = self._get_or_create_wrapping_key()
        timestamp: bytes = struct.pack(">d", time.time())
        plaintext: bytes = timestamp + key
        encrypted: bytes = Encryption(wrapping_key).encrypt(plaintext)
        self._write_restricted(self._key_path, encrypted)

    def _is_key_expired(self) -> bool:
        """Check if the cached key has expired (older than 12 hours).

        Returns:
            bool: True if the key file is missing, unreadable, or older than 12 hours.
        """
        if not os.path.exists(self._key_path):
            return True
        cached_data: tuple[float, bytes] | None = self._read_cached_key_data()
        if cached_data is None:
            return True
        timestamp, _ = cached_data
        return (time.time() - timestamp) > _KEY_SESSION_DURATION

    def replace_key_material(self, salt: bytes, key: bytes, n: int = _SCRYPT_N) -> None:
        """Replace all key material files for rekey operations.

        Removes old key material and writes new salt, verification token,
        cached key, and KDF parameters.

        Args:
            salt (bytes): The new salt.
            key (bytes): The new derived encryption key.
            n (int): The scrypt N cost parameter used to derive the key.
        """
        for filepath in [self._salt_path, self._verify_path, self._key_path]:
            if os.path.exists(filepath):
                os.remove(filepath)
        if self._params_path is not None and os.path.exists(self._params_path):
            os.remove(self._params_path)

        with self._atomic_writes() as written:
            self._write_restricted(self._salt_path, salt)
            written.append(self._salt_path)

            token: bytes = Encryption.create_verification_token(key)
            self._write_restricted(self._verify_path, token)
            written.append(self._verify_path)

            if not self._no_cache:
                self._cache_key(key)
                written.append(self._key_path)

            if self._params_path is not None:
                params_json: bytes = json.dumps({"n": n, "r": _SCRYPT_R, "p": _SCRYPT_P}).encode("utf-8")
                self._write_restricted(self._params_path, params_json)
                written.append(self._params_path)

    def _load_scrypt_n(self) -> int:
        """Load the scrypt N parameter from the KDF params file.

        Returns the value stored in the params file when available.
        Defaults to _SCRYPT_N when no params file is configured or present.

        Returns:
            int: The scrypt N cost parameter.
        """
        if self._params_path is not None and os.path.exists(self._params_path):
            with open(self._params_path, "r", encoding="utf-8") as fp:
                params: dict[str, int] = json.load(fp)
            return params.get("n", _SCRYPT_N)
        return _SCRYPT_N

    def verify_passphrase(self, passphrase: str) -> bool:
        """Verify a passphrase against the stored salt and verification token.

        Args:
            passphrase (str): The passphrase to verify.

        Returns:
            bool: True if the passphrase is correct, False otherwise.
        """
        return self._derive_and_verify(passphrase) is not None

    def _derive_and_verify(self, passphrase: str) -> bytes | None:
        """Derive a key from the passphrase and verify it against the token.

        Args:
            passphrase (str): The passphrase to verify.

        Returns:
            bytes | None: The derived key if verification succeeds, None otherwise.
        """
        with open(self._salt_path, "rb") as fp:
            salt: bytes = fp.read()
        with open(self._verify_path, "rb") as fp:
            token: bytes = fp.read()

        n: int = self._load_scrypt_n()
        key: bytes = Encryption.derive_key(passphrase, salt, n=n)
        if not Encryption.verify_key(key, token):
            return None
        return key
