"""Handles encryption and decryption of data at rest using AES-256-GCM."""

import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from gptcli.constants import GPTCLI_VERIFICATION_PLAINTEXT

_NONCE_SIZE: int = 12
_TAG_SIZE: int = 16
_KEY_SIZE: int = 32
_SALT_SIZE: int = 32
_SCRYPT_N: int = 2**17
_SCRYPT_R: int = 8
_SCRYPT_P: int = 1


class Encryption:
    """Provides AES-256-GCM encryption and decryption for data at rest.

    Attributes:
        _aesgcm: The AES-GCM cipher instance initialized with the provided key.
    """

    def __init__(self, key: bytes) -> None:
        """Initialize with a 256-bit encryption key.

        Args:
            key (bytes): A 32-byte encryption key.

        Raises:
            ValueError: If the key is not exactly 32 bytes.
        """
        if len(key) != _KEY_SIZE:
            raise ValueError(f"Key must be exactly {_KEY_SIZE} bytes, got {len(key)}.")
        self._aesgcm: AESGCM = AESGCM(key)

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext (bytes): The data to encrypt.

        Returns:
            bytes: The concatenation of nonce (12B) + ciphertext + GCM tag (16B).
        """
        nonce: bytes = os.urandom(_NONCE_SIZE)
        ciphertext: bytes = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    @staticmethod
    def _has_encrypted_content(ciphertext: bytes) -> bool:
        """Check if ciphertext is long enough to contain valid encrypted content.

        A valid ciphertext must hold at least a 12-byte nonce and a 16-byte GCM tag.

        Args:
            ciphertext (bytes): The raw ciphertext to check.

        Returns:
            bool: True if the ciphertext could contain valid encrypted content.
        """
        return len(ciphertext) >= _NONCE_SIZE + _TAG_SIZE

    def decrypt(self, ciphertext: bytes) -> bytes | None:
        """Decrypt ciphertext produced by encrypt().

        Args:
            ciphertext (bytes): The nonce + ciphertext + tag blob.

        Returns:
            bytes | None: The original plaintext, or None if decryption fails.
        """
        if not self._has_encrypted_content(ciphertext):
            return None
        nonce: bytes = ciphertext[:_NONCE_SIZE]
        encrypted_data: bytes = ciphertext[_NONCE_SIZE:]
        try:
            result: bytes = self._aesgcm.decrypt(nonce, encrypted_data, None)
            return result
        except InvalidTag:
            return None

    def encrypt_file(self, source_path: str) -> None:
        """Encrypt a file and write the result to source_path + '.enc'.

        The original file is removed after successful encryption.

        Args:
            source_path (str): Path to the plaintext file.

        Raises:
            FileNotFoundError: If the source file does not exist.
        """
        with open(source_path, "rb") as fp:
            plaintext: bytes = fp.read()
        encrypted: bytes = self.encrypt(plaintext)
        enc_path: str = source_path + ".enc"
        with open(enc_path, "wb") as fp:
            fp.write(encrypted)
        os.remove(source_path)

    def decrypt_file(self, source_path: str) -> bytes | None:
        """Decrypt an .enc file and return the plaintext bytes.

        Does NOT write the decrypted content to disk.

        Args:
            source_path (str): Path to the encrypted file (must end in '.enc').

        Returns:
            bytes | None: The decrypted plaintext content, or None if decryption fails.
        """
        if not source_path.endswith(".enc"):
            return None
        try:
            with open(source_path, "rb") as fp:
                ciphertext: bytes = fp.read()
        except FileNotFoundError:
            return None
        return self.decrypt(ciphertext)

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random 32-byte salt for key derivation.

        Returns:
            bytes: A 32-byte random salt.
        """
        return os.urandom(_SALT_SIZE)

    @staticmethod
    def derive_key(passphrase: str, salt: bytes, n: int = _SCRYPT_N) -> bytes:
        """Derive a 256-bit key from a passphrase and salt using scrypt.

        Args:
            passphrase (str): The user's passphrase.
            salt (bytes): A random salt for key derivation.
            n (int): The CPU/memory cost parameter for scrypt. Defaults to _SCRYPT_N (2**17).

        Returns:
            bytes: A 32-byte derived key.
        """
        kdf: Scrypt = Scrypt(salt=salt, length=_KEY_SIZE, n=n, r=_SCRYPT_R, p=_SCRYPT_P)
        key: bytes = kdf.derive(passphrase.encode("utf-8"))
        return key

    @staticmethod
    def create_verification_token(key: bytes) -> bytes:
        """Create a verification token by encrypting a known plaintext.

        Args:
            key (bytes): The encryption key to verify.

        Returns:
            bytes: The encrypted verification token.
        """
        enc: Encryption = Encryption(key=key)
        return enc.encrypt(GPTCLI_VERIFICATION_PLAINTEXT)

    @staticmethod
    def verify_key(key: bytes, token: bytes) -> bool:
        """Verify a key by attempting to decrypt a verification token.

        Args:
            key (bytes): The key to verify.
            token (bytes): The verification token created by create_verification_token().

        Returns:
            bool: True if the key is correct, False otherwise.
        """
        enc: Encryption = Encryption(key=key)
        plaintext: bytes | None = enc.decrypt(token)
        if plaintext is None:
            return False
        return hmac.compare_digest(plaintext, GPTCLI_VERIFICATION_PLAINTEXT)
