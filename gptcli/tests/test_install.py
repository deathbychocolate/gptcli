"""Holds tests for encryption migration in install.py."""

import contextlib
import os
from unittest.mock import patch

import pytest

from gptcli.src.common.encryption import Encryption
from gptcli.src.common.key_management import KeyManager
from gptcli.src.install import Migrate


class TestMigrationToEncrypted:

    @pytest.fixture
    def migrate_env(self, tmp_path: str) -> dict[str, str]:
        """Set up isolated paths for migration tests.

        Returns:
            dict[str, str]: Dictionary with encryption and provider paths.
        """
        return {
            "salt_path": os.path.join(str(tmp_path), ".salt"),
            "key_path": os.path.join(str(tmp_path), ".key"),
            "verify_path": os.path.join(str(tmp_path), ".verify.enc"),
            "kdf_params_path": os.path.join(str(tmp_path), ".kdf_params"),
            "mistral_dir": os.path.join(str(tmp_path), "mistral"),
            "openai_dir": os.path.join(str(tmp_path), "openai"),
        }

    @staticmethod
    def _apply_migrate_patches(
        env: dict[str, str], passphrase: str | None = "test-passphrase"
    ) -> contextlib.ExitStack:
        """Create and enter patches for migration tests.

        Args:
            env (dict[str, str]): The migrate_env fixture dictionary.
            passphrase (str | None): Return value for passphrase creation. Pass None to skip the patch.

        Returns:
            contextlib.ExitStack: A context manager with all patches applied.
        """
        stack = contextlib.ExitStack()
        km = KeyManager(
            salt_path=env["salt_path"],
            key_path=env["key_path"],
            verify_path=env["verify_path"],
            params_path=env["kdf_params_path"],
        )
        stack.enter_context(patch("gptcli.src.install.make_key_manager", return_value=km))
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_MISTRAL", env["mistral_dir"]))
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_OPENAI", env["openai_dir"]))
        if passphrase is not None:
            stack.enter_context(
                patch("gptcli.src.install.PassphrasePrompt.create_with_confirmation", return_value=passphrase)
            )
        return stack

    def test_detects_unencrypted_existing_installation(self, migrate_env: dict[str, str]) -> None:
        keys_dir = os.path.join(migrate_env["mistral_dir"], "keys")
        os.makedirs(keys_dir)
        with open(os.path.join(keys_dir, "main"), "w") as f:
            f.write("sk-test-key")

        with self._apply_migrate_patches(migrate_env):
            result = Migrate().to_encrypted()

        assert result is True

    def test_prompts_for_passphrase_during_migration(self, migrate_env: dict[str, str]) -> None:
        os.makedirs(migrate_env["mistral_dir"])

        with self._apply_migrate_patches(migrate_env, passphrase=None):
            with patch(
                "gptcli.src.install.PassphrasePrompt.create_with_confirmation", return_value="test-passphrase"
            ) as mock_prompt:
                Migrate().to_encrypted()

        mock_prompt.assert_called_once()

    def test_encrypts_existing_cleartext_files(self, migrate_env: dict[str, str]) -> None:
        keys_dir = os.path.join(migrate_env["mistral_dir"], "keys")
        os.makedirs(keys_dir)
        key_file = os.path.join(keys_dir, "main")
        with open(key_file, "w") as f:
            f.write("sk-test-key")

        with self._apply_migrate_patches(migrate_env):
            Migrate().to_encrypted()

        assert os.path.exists(key_file + ".enc")
        assert not os.path.exists(key_file)

    def test_creates_salt_verify_and_key_files(self, migrate_env: dict[str, str]) -> None:
        os.makedirs(migrate_env["mistral_dir"])

        with self._apply_migrate_patches(migrate_env):
            Migrate().to_encrypted()

        assert os.path.exists(migrate_env["salt_path"])
        assert os.path.exists(migrate_env["verify_path"])
        assert os.path.exists(migrate_env["key_path"])

    def test_skips_migration_when_already_encrypted(self, migrate_env: dict[str, str]) -> None:
        os.makedirs(migrate_env["mistral_dir"])

        km = KeyManager(
            salt_path=migrate_env["salt_path"],
            key_path=migrate_env["key_path"],
            verify_path=migrate_env["verify_path"],
        )
        km.initialize("existing-passphrase")

        with self._apply_migrate_patches(migrate_env, passphrase=None):
            result = Migrate().to_encrypted()

        assert result is False

    def test_existing_encrypted_data_remains_accessible_after_migration(self, migrate_env: dict[str, str]) -> None:
        keys_dir = os.path.join(migrate_env["mistral_dir"], "keys")
        os.makedirs(keys_dir)
        key_file = os.path.join(keys_dir, "main")
        original_content = "sk-test-key-12345"
        with open(key_file, "w") as f:
            f.write(original_content)

        with self._apply_migrate_patches(migrate_env):
            Migrate().to_encrypted()

        km = KeyManager(
            salt_path=migrate_env["salt_path"],
            key_path=migrate_env["key_path"],
            verify_path=migrate_env["verify_path"],
        )
        loaded_key = km.load_key()
        assert loaded_key is not None
        enc = Encryption(key=loaded_key)
        decrypted = enc.decrypt_file(key_file + ".enc")
        assert decrypted is not None
        assert decrypted.decode("utf-8") == original_content


class TestProviderInstaller:

    class TestIsAlreadyInstalled:

        def test_returns_true_when_marker_exists(self, tmp_path: str) -> None:
            from gptcli.src.install import ProviderInstaller

            marker = os.path.join(str(tmp_path), ".install_successful")
            with open(marker, "w") as f:
                f.write("")
            installer = ProviderInstaller(
                provider="test",
                storage_dirs=[],
                keys_dir=str(tmp_path),
                key_file=os.path.join(str(tmp_path), "key"),
                install_marker=marker,
                api_provider="test",
                default_model="model",
                default_role="role",
                message_factory=None,  # type: ignore[arg-type]
            )
            assert installer._is_already_installed() is True

        def test_returns_false_when_marker_missing(self, tmp_path: str) -> None:
            from gptcli.src.install import ProviderInstaller

            marker = os.path.join(str(tmp_path), ".install_successful")
            installer = ProviderInstaller(
                provider="test",
                storage_dirs=[],
                keys_dir=str(tmp_path),
                key_file=os.path.join(str(tmp_path), "key"),
                install_marker=marker,
                api_provider="test",
                default_model="model",
                default_role="role",
                message_factory=None,  # type: ignore[arg-type]
            )
            assert installer._is_already_installed() is False
