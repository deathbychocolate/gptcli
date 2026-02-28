"""Holds tests for main.py helper functions."""

import os
from unittest.mock import MagicMock

import pytest

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
)
from gptcli.main import (
    _key_file_for_provider,
    _read_encrypted_key,
    _read_plaintext_key,
)
from gptcli.src.common.constants import ProviderNames


# pylint: disable=W0212:protected-access
class TestKeyFileForProvider:
    """Tests for _key_file_for_provider()."""

    def test_returns_mistral_key_file_for_mistral_provider(self) -> None:
        result = _key_file_for_provider(ProviderNames.MISTRAL.value)
        assert result == GPTCLI_PROVIDER_MISTRAL_KEY_FILE

    def test_returns_openai_key_file_for_openai_provider(self) -> None:
        result = _key_file_for_provider(ProviderNames.OPENAI.value)
        assert result == GPTCLI_PROVIDER_OPENAI_KEY_FILE

    def test_raises_not_implemented_for_unsupported_provider(self) -> None:
        with pytest.raises(NotImplementedError):
            _key_file_for_provider("unsupported-provider")


class TestReadEncryptedKey:
    """Tests for _read_encrypted_key()."""

    def test_returns_decrypted_key(self, tmp_path: str) -> None:
        filepath = os.path.join(str(tmp_path), "key.enc")
        expected_key = "sk-test-api-key-123"
        mock_encryption = MagicMock()
        mock_encryption.decrypt_file.return_value = expected_key.encode("utf-8")

        result = _read_encrypted_key(filepath, mock_encryption)

        assert result == expected_key
        mock_encryption.decrypt_file.assert_called_once_with(filepath)

    def test_returns_empty_string_when_decryption_fails(self, tmp_path: str) -> None:
        filepath = os.path.join(str(tmp_path), "key.enc")
        mock_encryption = MagicMock()
        mock_encryption.decrypt_file.return_value = None

        result = _read_encrypted_key(filepath, mock_encryption)

        assert result == ""


class TestReadPlaintextKey:
    """Tests for _read_plaintext_key()."""

    def test_returns_key_from_file(self, tmp_path: str) -> None:
        filepath = os.path.join(str(tmp_path), "key")
        expected_key = "sk-test-api-key-456"
        with open(filepath, "w", encoding="utf8") as f:
            f.write(expected_key)

        result = _read_plaintext_key(filepath)

        assert result == expected_key

    def test_returns_empty_string_when_file_not_found(self) -> None:
        result = _read_plaintext_key("/nonexistent/path/key")
        assert result == ""
