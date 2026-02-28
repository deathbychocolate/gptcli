"""Holds all the tests for encryption_commands.py."""

import contextlib
import json
import logging
import os
from unittest.mock import patch

import pytest

from gptcli.src.common.encryption import Encryption
from gptcli.src.common.key_management import KeyManager
from gptcli.src.common.passphrase import PassphrasePrompt
from gptcli.src.modes.encryption_commands import EncryptionCommands


class TestEncryptionCommands:

    class TestEncryptProvider:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_encrypts_cleartext_json_files(self, encryption: Encryption, tmp_path: str) -> None:
            json_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(json_dir)
            filepath = os.path.join(json_dir, "100__2024_01_01__12_00_00__chat.json")
            with open(filepath, "w") as f:
                json.dump({"messages": []}, f)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.encrypt_provider()

            assert os.path.exists(filepath + ".enc")
            assert not os.path.exists(filepath)

        def test_encrypts_cleartext_key_file(self, encryption: Encryption, tmp_path: str) -> None:
            keys_dir = os.path.join(str(tmp_path), "keys")
            os.makedirs(keys_dir)
            filepath = os.path.join(keys_dir, "main")
            with open(filepath, "w") as f:
                f.write("sk-test-key-12345")

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.encrypt_provider()

            assert os.path.exists(filepath + ".enc")
            assert not os.path.exists(filepath)

        def test_encrypts_ocr_session_files(self, encryption: Encryption, tmp_path: str) -> None:
            ocr_dir = os.path.join(str(tmp_path), "storage", "ocr", "100__2024_01_01__12_00_00__ocr")
            os.makedirs(ocr_dir)
            for name, content in [("doc.md", b"# Title"), ("metadata.json", b"{}"), ("img.png", b"PNG data")]:
                with open(os.path.join(ocr_dir, name), "wb") as f:
                    f.write(content)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.encrypt_provider()

            for name in ["doc.md", "metadata.json", "img.png"]:
                assert os.path.exists(os.path.join(ocr_dir, name + ".enc"))
                assert not os.path.exists(os.path.join(ocr_dir, name))

        def test_skips_already_encrypted_files_with_log_message(
            self, encryption: Encryption, tmp_path: str, caplog: pytest.LogCaptureFixture
        ) -> None:
            filepath = os.path.join(str(tmp_path), "test.json.enc")
            with open(filepath, "wb") as f:
                f.write(b"encrypted data")

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            with caplog.at_level(logging.INFO):
                cmd.encrypt_provider()

            assert "Skipping already-encrypted" in caplog.text

        def test_does_not_modify_install_successful_marker(self, encryption: Encryption, tmp_path: str) -> None:
            marker = os.path.join(str(tmp_path), ".install_successful")
            with open(marker, "w") as f:
                f.write("")

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.encrypt_provider()

            assert os.path.exists(marker)
            assert not os.path.exists(marker + ".enc")

        def test_handles_empty_storage_directory(self, encryption: Encryption, tmp_path: str) -> None:
            storage_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(storage_dir)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.encrypt_provider()  # Should not raise

    class TestDecryptProvider:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_decrypts_enc_json_files(self, encryption: Encryption, tmp_path: str) -> None:
            json_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(json_dir)
            original_content = b'{"messages": []}'
            filepath = os.path.join(json_dir, "100__2024_01_01__12_00_00__chat.json")
            with open(filepath, "wb") as f:
                f.write(original_content)
            encryption.encrypt_file(filepath)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()

            assert os.path.exists(filepath)
            assert not os.path.exists(filepath + ".enc")
            with open(filepath, "rb") as f:
                assert f.read() == original_content

        def test_decrypts_enc_key_file(self, encryption: Encryption, tmp_path: str) -> None:
            keys_dir = os.path.join(str(tmp_path), "keys")
            os.makedirs(keys_dir)
            original_content = b"sk-test-key-12345"
            filepath = os.path.join(keys_dir, "main")
            with open(filepath, "wb") as f:
                f.write(original_content)
            encryption.encrypt_file(filepath)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()

            assert os.path.exists(filepath)
            with open(filepath, "rb") as f:
                assert f.read() == original_content

        def test_decrypts_enc_ocr_session_files(self, encryption: Encryption, tmp_path: str) -> None:
            ocr_dir = os.path.join(str(tmp_path), "storage", "ocr", "100__2024_01_01__12_00_00__ocr")
            os.makedirs(ocr_dir)
            files = {"doc.md": b"# Title", "metadata.json": b"{}", "img.png": b"PNG data"}
            for name, content in files.items():
                filepath = os.path.join(ocr_dir, name)
                with open(filepath, "wb") as f:
                    f.write(content)
                encryption.encrypt_file(filepath)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()

            for name, content in files.items():
                filepath = os.path.join(ocr_dir, name)
                assert os.path.exists(filepath)
                with open(filepath, "rb") as f:
                    assert f.read() == content

        def test_skips_non_enc_files_with_log_message(
            self, encryption: Encryption, tmp_path: str, caplog: pytest.LogCaptureFixture
        ) -> None:
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w") as f:
                f.write("{}")

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            with caplog.at_level(logging.INFO):
                cmd.decrypt_provider()

            assert "Skipping non-encrypted" in caplog.text

        def test_handles_empty_storage_directory(self, encryption: Encryption, tmp_path: str) -> None:
            storage_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(storage_dir)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()  # Should not raise

        def test_no_tmp_files_remain_after_decrypt(self, encryption: Encryption, tmp_path: str) -> None:
            json_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(json_dir)
            filepath = os.path.join(json_dir, "100__2024_01_01__12_00_00__chat.json")
            with open(filepath, "wb") as f:
                f.write(b'{"messages": []}')
            encryption.encrypt_file(filepath)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()

            for dirpath, _, filenames in os.walk(str(tmp_path)):
                for filename in filenames:
                    assert not filename.endswith(".tmp"), f"Temp file not cleaned up: {filename}"

        def test_cleartext_file_is_complete_after_decrypt(self, encryption: Encryption, tmp_path: str) -> None:
            json_dir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(json_dir)
            original_content = b'{"messages": [{"role": "user", "content": "hello"}]}'
            filepath = os.path.join(json_dir, "100__2024_01_01__12_00_00__chat.json")
            with open(filepath, "wb") as f:
                f.write(original_content)
            encryption.encrypt_file(filepath)

            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            cmd.decrypt_provider()

            with open(filepath, "rb") as f:
                assert f.read() == original_content

    class TestRekey:

        @pytest.fixture
        def rekey_env(self, tmp_path: str) -> dict[str, str]:
            """Set up isolated paths for rekey tests.

            Returns:
                dict[str, str]: Dictionary with salt_path, key_path, verify_path, and provider_dir.
            """
            provider_dir = os.path.join(str(tmp_path), "provider")
            os.makedirs(provider_dir)
            return {
                "salt_path": os.path.join(str(tmp_path), ".salt"),
                "key_path": os.path.join(str(tmp_path), ".key"),
                "verify_path": os.path.join(str(tmp_path), ".verify.enc"),
                "kdf_params_path": os.path.join(str(tmp_path), ".kdf_params"),
                "provider_dir": provider_dir,
            }

        @staticmethod
        def _apply_rekey_patches(
            env: dict[str, str],
            old_passphrase: str = "old-pass",
            new_passphrase: str | None = "new-pass",
            verify_return: bool = True,
        ) -> contextlib.ExitStack:
            """Create and enter patches for rekey tests.

            Args:
                env (dict[str, str]): The rekey_env fixture dictionary.
                old_passphrase (str): Return value for the old passphrase prompt.
                new_passphrase (str | None): Return value for new passphrase creation.
                verify_return (bool): Return value for verify_passphrase.

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
            stack.enter_context(patch("gptcli.src.modes.encryption_commands.make_key_manager", return_value=km))
            stack.enter_context(patch.object(PassphrasePrompt, "prompt", return_value=old_passphrase))
            stack.enter_context(patch.object(KeyManager, "verify_passphrase", return_value=verify_return))
            stack.enter_context(
                patch(
                    "gptcli.src.modes.encryption_commands.PassphrasePrompt.create_with_confirmation",
                    return_value=new_passphrase,
                )
            )
            return stack

        def test_reencrypts_all_files_with_new_key(self, rekey_env: dict[str, str]) -> None:
            old_key = os.urandom(32)
            old_enc = Encryption(key=old_key)

            keys_dir = os.path.join(rekey_env["provider_dir"], "keys")
            os.makedirs(keys_dir)
            filepath = os.path.join(keys_dir, "main")
            with open(filepath, "wb") as f:
                f.write(b"my-api-key")
            old_enc.encrypt_file(filepath)

            with self._apply_rekey_patches(rekey_env):
                EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]])

            km = KeyManager(
                salt_path=rekey_env["salt_path"], key_path=rekey_env["key_path"], verify_path=rekey_env["verify_path"]
            )
            new_key = km.load_key()
            assert new_key is not None
            new_enc = Encryption(key=new_key)
            decrypted = new_enc.decrypt_file(os.path.join(keys_dir, "main.enc"))
            assert decrypted == b"my-api-key"

        def test_updates_salt_file(self, rekey_env: dict[str, str]) -> None:
            old_enc = Encryption(key=os.urandom(32))

            with open(rekey_env["salt_path"], "wb") as f:
                f.write(os.urandom(32))
            with open(rekey_env["salt_path"], "rb") as f:
                old_salt = f.read()

            with self._apply_rekey_patches(rekey_env):
                EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]])

            with open(rekey_env["salt_path"], "rb") as f:
                new_salt = f.read()
            assert old_salt != new_salt

        def test_updates_verify_and_key_cache(self, rekey_env: dict[str, str]) -> None:
            old_enc = Encryption(key=os.urandom(32))

            with self._apply_rekey_patches(rekey_env):
                EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]])

            assert os.path.exists(rekey_env["verify_path"])
            assert os.path.exists(rekey_env["key_path"])
            with open(rekey_env["key_path"], "rb") as f:
                cached_key = f.read()
            assert len(cached_key) > 40  # encrypted: nonce + ciphertext(timestamp + key) + tag

        def test_old_key_no_longer_decrypts_files(self, rekey_env: dict[str, str]) -> None:
            old_key = os.urandom(32)
            old_enc = Encryption(key=old_key)

            keys_dir = os.path.join(rekey_env["provider_dir"], "keys")
            os.makedirs(keys_dir)
            filepath = os.path.join(keys_dir, "main")
            with open(filepath, "wb") as f:
                f.write(b"my-api-key")
            old_enc.encrypt_file(filepath)

            with self._apply_rekey_patches(rekey_env):
                EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]])

            assert old_enc.decrypt_file(os.path.join(keys_dir, "main.enc")) is None

        def test_returns_false_when_new_passphrase_aborted(self, rekey_env: dict[str, str]) -> None:
            old_enc = Encryption(key=os.urandom(32))

            with (
                patch.object(PassphrasePrompt, "prompt", return_value="old-pass"),
                patch.object(KeyManager, "verify_passphrase"),
                patch(
                    "gptcli.src.modes.encryption_commands.PassphrasePrompt.create_with_confirmation",
                    return_value=None,
                ),
            ):
                assert EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]]) is False

        def test_rekey_rejects_wrong_old_passphrase(self, rekey_env: dict[str, str]) -> None:
            old_enc = Encryption(key=os.urandom(32))

            with (
                patch.object(PassphrasePrompt, "prompt", return_value="wrong-pass"),
                patch.object(KeyManager, "verify_passphrase", return_value=False),
            ):
                assert EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]]) is False

        def test_rekey_cleans_up_temp_files_on_failure(self, rekey_env: dict[str, str]) -> None:
            old_key = os.urandom(32)
            old_enc = Encryption(key=old_key)

            keys_dir = os.path.join(rekey_env["provider_dir"], "keys")
            os.makedirs(keys_dir)

            for name in ["main", "backup"]:
                filepath = os.path.join(keys_dir, name)
                with open(filepath, "wb") as f:
                    f.write(b"api-key-data")
                old_enc.encrypt_file(filepath)

            original_decrypt_file = old_enc.decrypt_file
            call_count = 0

            def failing_decrypt(path: str) -> bytes | None:
                nonlocal call_count
                call_count += 1
                if call_count > 1:
                    raise RuntimeError("Simulated failure")
                return original_decrypt_file(path)

            with self._apply_rekey_patches(rekey_env):
                with patch.object(old_enc, "decrypt_file", side_effect=failing_decrypt):
                    with pytest.raises(RuntimeError, match="Simulated failure"):
                        EncryptionCommands.rekey(old_encryption=old_enc, providers=[rekey_env["provider_dir"]])

            for dirpath, _, filenames in os.walk(rekey_env["provider_dir"]):
                for filename in filenames:
                    assert not filename.endswith(".enc.new"), f"Temp file not cleaned up: {filename}"

            assert os.path.exists(os.path.join(keys_dir, "main.enc"))
            assert os.path.exists(os.path.join(keys_dir, "backup.enc"))

    class TestCollectFiles:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_includes_files_matching_predicate(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w") as f:
                f.write("{}")
            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            result = cmd._collect_files(include=lambda f: f.endswith(".json"), skip_log="Skipping")
            assert filepath in result

        def test_excludes_files_not_matching_predicate(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w") as f:
                f.write("{}")
            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            result = cmd._collect_files(include=lambda f: f.endswith(".enc"), skip_log="Skipping")
            assert filepath not in result

        def test_skips_install_marker_file(self, encryption: Encryption, tmp_path: str) -> None:
            marker = os.path.join(str(tmp_path), ".install_successful")
            with open(marker, "w") as f:
                f.write("")
            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            result = cmd._collect_files(include=lambda f: True, skip_log="Skipping")
            assert marker not in result

        def test_logs_skipped_files(
            self, encryption: Encryption, tmp_path: str, caplog: pytest.LogCaptureFixture
        ) -> None:
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "w") as f:
                f.write("data")
            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            with caplog.at_level(logging.INFO):
                cmd._collect_files(include=lambda f: False, skip_log="Skipping non-matching file")
            assert "Skipping non-matching file" in caplog.text

        def test_walks_subdirectories(self, encryption: Encryption, tmp_path: str) -> None:
            subdir = os.path.join(str(tmp_path), "storage", "json")
            os.makedirs(subdir)
            filepath = os.path.join(subdir, "chat.json")
            with open(filepath, "w") as f:
                f.write("{}")
            cmd = EncryptionCommands(provider_dir=str(tmp_path), encryption=encryption)
            result = cmd._collect_files(include=lambda f: f.endswith(".json"), skip_log="Skipping")
            assert filepath in result

    class TestCliRouting:

        def test_all_encrypt_routes_to_all_providers(self) -> None:
            from gptcli.src.cli import CommandParser

            with patch("sys.argv", ["gptcli", "all", "encrypt"]):
                parser = CommandParser()
                assert parser.args.provider == "all"
                assert parser.args.mode_name == "encrypt"

        def test_rekey_command_parsed_for_all(self) -> None:
            from gptcli.src.cli import CommandParser

            with patch("sys.argv", ["gptcli", "all", "rekey"]):
                parser = CommandParser()
                assert parser.args.provider == "all"
                assert parser.args.mode_name == "rekey"
