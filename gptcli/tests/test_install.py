"""Holds tests for encryption migration and opaque storage migration in install.py."""

import contextlib
import json
import os
from typing import Any
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


class TestMigrateToOpaqueStorage:

    @pytest.fixture
    def storage_env(self, tmp_path: str) -> dict[str, str]:
        """Create isolated provider storage directories."""
        openai_storage = os.path.join(str(tmp_path), "openai", "storage")
        mistral_storage = os.path.join(str(tmp_path), "mistral", "storage")
        return {
            "tmp_path": str(tmp_path),
            "openai_storage": openai_storage,
            "openai_json": os.path.join(openai_storage, "json"),
            "openai_chat": os.path.join(openai_storage, "chat"),
            "openai_ocr": os.path.join(openai_storage, "ocr"),
            "mistral_storage": mistral_storage,
            "mistral_json": os.path.join(mistral_storage, "json"),
            "mistral_chat": os.path.join(mistral_storage, "chat"),
            "mistral_ocr": os.path.join(mistral_storage, "ocr"),
        }

    @staticmethod
    def _apply_opaque_patches(env: dict[str, str]) -> contextlib.ExitStack:
        """Patch provider constants for opaque storage migration tests."""
        stack = contextlib.ExitStack()
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_OPENAI_STORAGE_DIR", env["openai_storage"]))
        stack.enter_context(
            patch("gptcli.src.install.GPTCLI_PROVIDER_OPENAI_STORAGE_LEGACY_JSON_DIR", env["openai_json"])
        )
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR", env["openai_chat"]))
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR", env["mistral_storage"]))
        stack.enter_context(
            patch("gptcli.src.install.GPTCLI_PROVIDER_MISTRAL_STORAGE_LEGACY_JSON_DIR", env["mistral_json"])
        )
        stack.enter_context(patch("gptcli.src.install.GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR", env["mistral_chat"]))
        return stack

    def test_renames_json_to_chat(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_json"])
        with open(os.path.join(storage_env["openai_json"], "test.txt"), "w") as f:
            f.write("test")

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        assert os.path.isdir(storage_env["openai_chat"])
        assert not os.path.isdir(storage_env["openai_json"])

    def test_skips_rename_when_chat_already_exists(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_json"])
        os.makedirs(storage_env["openai_chat"])
        with open(os.path.join(storage_env["openai_json"], "old.txt"), "w") as f:
            f.write("old")
        with open(os.path.join(storage_env["openai_chat"], "new.txt"), "w") as f:
            f.write("new")

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        # json/ should still exist since chat/ was already present
        assert os.path.isdir(storage_env["openai_json"])
        assert os.path.isdir(storage_env["openai_chat"])

    def test_migrates_chat_files_to_uuid_dirs(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_chat"])
        chat_data: dict[str, list[dict[str, Any]]] = {"messages": [{"role": "user", "content": "Hello"}]}
        chat_file = os.path.join(storage_env["openai_chat"], "1733422696__2024_12_05__18_18_16__chat.json")
        with open(chat_file, "w", encoding="utf8") as f:
            json.dump(chat_data, f)

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        # Original file should be gone
        assert not os.path.exists(chat_file)

        # UUID directory should exist with session.json
        subdirs = [
            d
            for d in os.listdir(storage_env["openai_chat"])
            if os.path.isdir(os.path.join(storage_env["openai_chat"], d))
        ]
        assert len(subdirs) == 1
        session_dir = os.path.join(storage_env["openai_chat"], subdirs[0])
        assert os.path.exists(os.path.join(session_dir, "session.json"))
        assert os.path.exists(os.path.join(session_dir, "metadata.json"))

    def test_creates_chat_manifest(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_chat"])
        chat_file = os.path.join(storage_env["openai_chat"], "1733422696__2024_12_05__18_18_16__chat.json")
        with open(chat_file, "w", encoding="utf8") as f:
            json.dump({"messages": []}, f)

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        manifest_path = os.path.join(storage_env["openai_chat"], ".manifest.json")
        assert os.path.exists(manifest_path)
        with open(manifest_path, "r", encoding="utf8") as f:
            entries = json.load(f)
        assert len(entries) == 1
        assert entries[0]["created"] == 1733422696.0

    def test_migrates_ocr_dirs_to_uuid_dirs(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_ocr"])
        ocr_dir = os.path.join(storage_env["openai_ocr"], "1733422696__2024_12_05__18_18_16__ocr")
        os.makedirs(ocr_dir)
        with open(os.path.join(ocr_dir, "doc.md"), "w") as f:
            f.write("# Test")
        metadata = {"ocr": {"created": 1733422696.0, "uuid": "old-uuid"}}
        with open(os.path.join(ocr_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f)

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        # Old dir should be gone
        assert not os.path.exists(ocr_dir)

        # UUID dir should exist
        subdirs = [
            d
            for d in os.listdir(storage_env["openai_ocr"])
            if os.path.isdir(os.path.join(storage_env["openai_ocr"], d))
        ]
        assert len(subdirs) == 1

        # Manifest should exist
        manifest_path = os.path.join(storage_env["openai_ocr"], ".manifest.json")
        assert os.path.exists(manifest_path)

    def test_idempotent_no_changes_on_second_run(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_chat"])
        chat_file = os.path.join(storage_env["openai_chat"], "100__2024_01_01__12_00_00__chat.json")
        with open(chat_file, "w", encoding="utf8") as f:
            json.dump({"messages": []}, f)

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()
            # Count items after first run
            items_after_first = os.listdir(storage_env["openai_chat"])
            Migrate.migrate_to_opaque_storage()
            items_after_second = os.listdir(storage_env["openai_chat"])

        assert sorted(items_after_first) == sorted(items_after_second)

    def test_skips_when_no_storage_dir(self, storage_env: dict[str, str]) -> None:
        # Don't create any dirs
        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()  # Should not raise

    def test_migrates_encrypted_chat_files(self, storage_env: dict[str, str]) -> None:
        os.makedirs(storage_env["openai_chat"])
        chat_file = os.path.join(storage_env["openai_chat"], "100__2024_01_01__12_00_00__chat.json.enc")
        with open(chat_file, "wb") as f:
            f.write(b"encrypted data")

        with self._apply_opaque_patches(storage_env):
            Migrate.migrate_to_opaque_storage()

        assert not os.path.exists(chat_file)
        subdirs = [
            d
            for d in os.listdir(storage_env["openai_chat"])
            if os.path.isdir(os.path.join(storage_env["openai_chat"], d))
        ]
        assert len(subdirs) == 1
        session_dir = os.path.join(storage_env["openai_chat"], subdirs[0])
        assert os.path.exists(os.path.join(session_dir, "session.json.enc"))
