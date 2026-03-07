"""Shared file I/O utilities for reading plaintext and encrypted files."""

import os

from gptcli.src.common.encryption import Encryption


def read_text_file(filepath: str, encryption: Encryption | None) -> str | None:
    """Read text from a plaintext or encrypted file, returning None on any failure.

    Prefers the encrypted file (filepath + '.enc') when it exists. Returns None
    silently if the encrypted file exists but no encryption instance is provided,
    or if decryption fails.

    Args:
        filepath (str): Path to the plaintext file (without .enc suffix).
        encryption (Encryption | None): Encryption instance for decryption, or None.

    Returns:
        str | None: The file contents as text, or None if unavailable.
    """
    enc_path = filepath + ".enc"
    if os.path.exists(enc_path):
        if encryption is None:
            return None
        decrypted = encryption.decrypt_file(enc_path)
        return decrypted.decode("utf-8") if decrypted is not None else None
    try:
        with open(filepath, "r", encoding="utf-8") as fp:
            return fp.read()
    except FileNotFoundError:
        return None
