"""Holds all the tests for key_management.py."""

import os
import stat
import struct
import time
from unittest.mock import patch

import pytest

from gptcli.src.common.key_management import (
    _KEY_SESSION_DURATION,
    _KEY_SIZE,
    _TIMESTAMP_SIZE,
    KeyManager,
    make_key_manager,
)
from gptcli.src.common.passphrase import PassphrasePrompt


def _make_km(tmp_path: str, no_cache: bool = False, params_path: str | None = None) -> KeyManager:
    """Create a KeyManager with all paths inside tmp_path.

    Args:
        tmp_path (str): The temporary directory for test files.
        no_cache (bool): If True, disable key caching.
        params_path (str | None): Optional path to KDF params file. If None, no params file is used.

    Returns:
        KeyManager: A KeyManager configured for testing.
    """
    return KeyManager(
        salt_path=os.path.join(str(tmp_path), ".salt"),
        key_path=os.path.join(str(tmp_path), ".key"),
        verify_path=os.path.join(str(tmp_path), ".verify.enc"),
        params_path=params_path,
        wrapping_key_path=os.path.join(str(tmp_path), "wrapping.key"),
        no_cache=no_cache,
    )


class TestKeyManager:

    class TestIsInitialized:

        def test_returns_false_when_no_files_exist(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            assert km.is_initialized() is False

        def test_returns_false_when_only_salt_exists(self, tmp_path: str) -> None:
            salt_path = os.path.join(str(tmp_path), ".salt")
            with open(salt_path, "wb") as f:
                f.write(os.urandom(32))
            km = _make_km(tmp_path)
            assert km.is_initialized() is False

        def test_returns_true_when_salt_and_verify_exist(self, tmp_path: str) -> None:
            salt_path = os.path.join(str(tmp_path), ".salt")
            verify_path = os.path.join(str(tmp_path), ".verify.enc")
            with open(salt_path, "wb") as f:
                f.write(os.urandom(32))
            with open(verify_path, "wb") as f:
                f.write(os.urandom(44))
            km = _make_km(tmp_path)
            assert km.is_initialized() is True

    class TestInitialize:

        def test_salt_file_exists_after_initialization(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            assert os.path.exists(os.path.join(str(tmp_path), ".salt"))

        def test_verification_token_exists_after_initialization(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            assert os.path.exists(os.path.join(str(tmp_path), ".verify.enc"))

        def test_key_cache_exists_after_initialization(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            assert os.path.exists(os.path.join(str(tmp_path), ".key"))

        def test_key_cache_is_owner_readable_only(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            key_path = os.path.join(str(tmp_path), ".key")
            mode = os.stat(key_path).st_mode
            assert stat.S_IMODE(mode) == 0o600

        def test_returns_32_byte_key(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            key = km.initialize("test-passphrase")
            assert len(key) == 32

        def test_raises_if_already_initialized(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            with pytest.raises(RuntimeError):
                km.initialize("test-passphrase")

    class TestLoadKey:

        def test_returns_cached_key_when_key_file_exists(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            loaded_key = km.load_key()
            assert loaded_key == original_key

        def test_prompts_for_passphrase_when_no_key_file(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            os.remove(os.path.join(str(tmp_path), ".key"))
            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"):
                loaded_key = km.load_key()
            assert loaded_key == original_key

        def test_caches_key_after_successful_passphrase_entry(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            key_path = os.path.join(str(tmp_path), ".key")
            os.remove(key_path)
            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"):
                km.load_key()
            assert os.path.exists(key_path)

        def test_returns_none_after_max_incorrect_passphrase_attempts(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("correct-passphrase")
            os.remove(os.path.join(str(tmp_path), ".key"))
            with patch.object(PassphrasePrompt, "prompt", return_value="wrong-passphrase"):
                assert km.load_key() is None

        def test_removes_expired_key_and_prompts(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")

            # Simulate expiry by patching time.time to return a future value
            future_time = time.time() + _KEY_SESSION_DURATION + 1
            with (
                patch("gptcli.src.common.key_management.time.time", return_value=future_time),
                patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"),
            ):
                loaded_key = km.load_key()
            assert loaded_key == original_key

        def test_returns_none_when_wrapping_key_missing(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")

            # Remove the wrapping key to simulate post-reboot
            wrapping_key_path = os.path.join(str(tmp_path), "wrapping.key")
            os.remove(wrapping_key_path)

            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"):
                loaded_key = km.load_key()
            # Key file should have been removed, passphrase re-derived
            assert loaded_key is not None
            assert len(loaded_key) == _KEY_SIZE

    class TestCacheKey:

        def test_file_is_encrypted(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            key = os.urandom(32)
            km._cache_key(key)
            key_path = os.path.join(str(tmp_path), ".key")
            with open(key_path, "rb") as f:
                data = f.read()
            # The raw timestamp+key should not appear in the encrypted file
            timestamp = struct.pack(">d", time.time())
            raw_payload = timestamp + key
            assert data != raw_payload
            # Encrypted file should be larger than raw payload (nonce + tag overhead)
            assert len(data) > _TIMESTAMP_SIZE + _KEY_SIZE

        def test_file_has_0600_permissions(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km._cache_key(os.urandom(32))
            key_path = os.path.join(str(tmp_path), ".key")
            mode = os.stat(key_path).st_mode
            assert stat.S_IMODE(mode) == 0o600

    class TestIsKeyExpired:

        def test_returns_true_when_no_key_file(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            assert km._is_key_expired() is True

        def test_returns_false_for_fresh_key(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km._cache_key(os.urandom(32))
            assert km._is_key_expired() is False

        def test_returns_true_for_expired_key(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km._cache_key(os.urandom(32))
            future_time = time.time() + _KEY_SESSION_DURATION + 1
            with patch("gptcli.src.common.key_management.time.time", return_value=future_time):
                assert km._is_key_expired() is True

        def test_returns_true_when_wrapping_key_missing(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km._cache_key(os.urandom(32))
            os.remove(os.path.join(str(tmp_path), "wrapping.key"))
            assert km._is_key_expired() is True

    class TestReplaceKeyMaterial:

        def test_writes_new_key_material(self, tmp_path: str) -> None:
            km = _make_km(tmp_path, params_path=os.path.join(str(tmp_path), ".kdf_params"))
            from gptcli.src.common.encryption import Encryption

            salt = Encryption.generate_salt()
            key = Encryption.derive_key("test-passphrase-long", salt)
            km.replace_key_material(salt=salt, key=key)
            assert os.path.exists(os.path.join(str(tmp_path), ".salt"))
            assert os.path.exists(os.path.join(str(tmp_path), ".verify.enc"))
            assert os.path.exists(os.path.join(str(tmp_path), ".key"))

    class TestVerifyPassphrase:

        def test_returns_true_on_correct_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            assert km.verify_passphrase("test-passphrase") is True

        def test_returns_false_on_incorrect_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("correct-passphrase")
            assert km.verify_passphrase("wrong-passphrase") is False

    class TestDeriveAndVerify:

        def test_returns_key_on_correct_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            result = km._derive_and_verify("test-passphrase")
            assert result == original_key

        def test_returns_none_on_incorrect_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("correct-passphrase")
            assert km._derive_and_verify("wrong-passphrase") is None

    class TestGetVolatileDir:

        def test_returns_dev_shm_on_linux_when_available(self, tmp_path: str) -> None:
            with (
                patch("gptcli.src.common.key_management.sys.platform", "linux"),
                patch("gptcli.src.common.key_management.os.path.isdir", return_value=True),
            ):
                assert KeyManager._get_volatile_dir() == "/dev/shm"

        def test_falls_back_to_tempdir_on_linux_without_dev_shm(self, tmp_path: str) -> None:
            with (
                patch("gptcli.src.common.key_management.sys.platform", "linux"),
                patch("gptcli.src.common.key_management.os.path.isdir", return_value=False),
                patch("gptcli.src.common.key_management.tempfile.gettempdir", return_value="/tmp"),
            ):
                assert KeyManager._get_volatile_dir() == "/tmp"

        def test_returns_tempdir_on_macos(self, tmp_path: str) -> None:
            with (
                patch("gptcli.src.common.key_management.sys.platform", "darwin"),
                patch("gptcli.src.common.key_management.tempfile.gettempdir", return_value="/var/folders/xx/yy"),
            ):
                assert KeyManager._get_volatile_dir() == "/var/folders/xx/yy"

    class TestWrappingKey:

        def test_creates_wrapping_key_file(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            wrapping_key = km._get_or_create_wrapping_key()
            assert len(wrapping_key) == 32
            wrapping_key_path = os.path.join(str(tmp_path), "wrapping.key")
            assert os.path.exists(wrapping_key_path)

        def test_wrapping_key_has_0600_permissions(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km._get_or_create_wrapping_key()
            wrapping_key_path = os.path.join(str(tmp_path), "wrapping.key")
            mode = os.stat(wrapping_key_path).st_mode
            assert stat.S_IMODE(mode) == 0o600

        def test_returns_same_key_on_second_call(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            key1 = km._get_or_create_wrapping_key()
            key2 = km._get_or_create_wrapping_key()
            assert key1 == key2

        def test_read_returns_none_when_missing(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            assert km._read_wrapping_key() is None

        def test_read_returns_none_for_wrong_size(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            wrapping_key_path = os.path.join(str(tmp_path), "wrapping.key")
            with open(wrapping_key_path, "wb") as f:
                f.write(b"short")
            assert km._read_wrapping_key() is None

    class TestAtomicWrites:

        def test_files_persist_on_success(self, tmp_path: str) -> None:
            file_a = os.path.join(str(tmp_path), "a.txt")
            file_b = os.path.join(str(tmp_path), "b.txt")
            with KeyManager._atomic_writes() as written:
                with open(file_a, "w") as f:
                    f.write("a")
                written.append(file_a)
                with open(file_b, "w") as f:
                    f.write("b")
                written.append(file_b)
            assert os.path.exists(file_a)
            assert os.path.exists(file_b)

        def test_removes_all_files_on_failure(self, tmp_path: str) -> None:
            file_a = os.path.join(str(tmp_path), "a.txt")
            file_b = os.path.join(str(tmp_path), "b.txt")
            with pytest.raises(RuntimeError):
                with KeyManager._atomic_writes() as written:
                    with open(file_a, "w") as f:
                        f.write("a")
                    written.append(file_a)
                    with open(file_b, "w") as f:
                        f.write("b")
                    written.append(file_b)
                    raise RuntimeError("simulated failure")
            assert not os.path.exists(file_a)
            assert not os.path.exists(file_b)

        def test_removes_only_written_files_on_failure(self, tmp_path: str) -> None:
            file_a = os.path.join(str(tmp_path), "a.txt")
            file_b = os.path.join(str(tmp_path), "b.txt")
            with pytest.raises(RuntimeError):
                with KeyManager._atomic_writes() as written:
                    with open(file_a, "w") as f:
                        f.write("a")
                    written.append(file_a)
                    raise RuntimeError("simulated failure before b")
            assert not os.path.exists(file_a)
            assert not os.path.exists(file_b)

        def test_re_raises_original_exception(self, tmp_path: str) -> None:
            with pytest.raises(ValueError, match="specific error"):
                with KeyManager._atomic_writes() as written:
                    written.append(os.path.join(str(tmp_path), "a.txt"))
                    raise ValueError("specific error")

    class TestNoCacheMode:

        def test_initialize_does_not_create_key_file(self, tmp_path: str) -> None:
            km = _make_km(tmp_path, no_cache=True)
            km.initialize("test-passphrase")
            assert not os.path.exists(os.path.join(str(tmp_path), ".key"))

        def test_initialize_does_not_create_wrapping_key(self, tmp_path: str) -> None:
            km = _make_km(tmp_path, no_cache=True)
            km.initialize("test-passphrase")
            assert not os.path.exists(os.path.join(str(tmp_path), "wrapping.key"))

        def test_load_key_skips_cache_and_always_prompts(self, tmp_path: str) -> None:
            # Initialize with caching to create a .key file
            km_cached = _make_km(tmp_path, no_cache=False)
            original_key = km_cached.initialize("test-passphrase")
            assert os.path.exists(os.path.join(str(tmp_path), ".key"))

            # Now create a no-cache manager; it should ignore the existing .key and prompt
            km_no_cache = _make_km(tmp_path, no_cache=True)
            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase") as mock_prompt:
                loaded_key = km_no_cache.load_key()
            mock_prompt.assert_called_once()
            assert loaded_key == original_key

        def test_load_key_does_not_write_key_file_after_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path, no_cache=True)
            km.initialize("test-passphrase")
            assert not os.path.exists(os.path.join(str(tmp_path), ".key"))

            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"):
                km.load_key()
            assert not os.path.exists(os.path.join(str(tmp_path), ".key"))

    class TestReadCachedKeyData:

        def test_returns_timestamp_and_key_bytes_for_valid_cache(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            result = km._read_cached_key_data()
            assert result is not None
            timestamp, key_bytes = result
            assert isinstance(timestamp, float)
            assert key_bytes == original_key

        def test_returns_none_when_wrapping_key_missing(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            os.remove(os.path.join(str(tmp_path), "wrapping.key"))
            assert km._read_cached_key_data() is None

        def test_returns_none_when_cache_file_corrupted(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            key_path = os.path.join(str(tmp_path), ".key")
            with open(key_path, "wb") as f:
                f.write(b"corrupted data that is not valid encrypted content at all")
            assert km._read_cached_key_data() is None

        def test_removes_cache_file_on_decryption_failure(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            key_path = os.path.join(str(tmp_path), ".key")
            with open(key_path, "wb") as f:
                f.write(os.urandom(100))
            km._read_cached_key_data()
            assert not os.path.exists(key_path)

    class TestLoadFromCache:

        def test_returns_key_when_cache_is_valid(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            assert km._load_from_cache() == original_key

        def test_returns_none_when_no_cache_mode(self, tmp_path: str) -> None:
            km_cached = _make_km(tmp_path, no_cache=False)
            km_cached.initialize("test-passphrase")
            km_no_cache = _make_km(tmp_path, no_cache=True)
            assert km_no_cache._load_from_cache() is None

        def test_returns_none_when_no_key_file_exists(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            assert km._load_from_cache() is None

        def test_returns_none_and_removes_expired_cache(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            key_path = os.path.join(str(tmp_path), ".key")
            future_time = time.time() + _KEY_SESSION_DURATION + 1
            with patch("gptcli.src.common.key_management.time.time", return_value=future_time):
                assert km._load_from_cache() is None
            assert not os.path.exists(key_path)

    class TestPromptForKey:

        def test_returns_key_on_correct_passphrase(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            original_key = km.initialize("test-passphrase")
            with patch.object(PassphrasePrompt, "prompt", return_value="test-passphrase"):
                assert km._prompt_for_key() == original_key

        def test_returns_none_when_user_aborts(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("test-passphrase")
            with patch.object(PassphrasePrompt, "prompt", return_value=None):
                assert km._prompt_for_key() is None

        def test_returns_none_after_max_incorrect_attempts(self, tmp_path: str) -> None:
            km = _make_km(tmp_path)
            km.initialize("correct-passphrase")
            with patch.object(PassphrasePrompt, "prompt", return_value="wrong-passphrase"):
                assert km._prompt_for_key() is None

    class TestMakeKeyManager:

        def test_returns_key_manager_instance(self) -> None:
            km = make_key_manager()
            assert isinstance(km, KeyManager)

        def test_respects_no_cache_parameter(self) -> None:
            km = make_key_manager(no_cache=True)
            assert km._no_cache is True

        def test_uses_standard_paths(self) -> None:
            from gptcli.constants import (
                GPTCLI_KDF_PARAMS_FILE,
                GPTCLI_KEY_CACHE_FILE,
                GPTCLI_SALT_FILE,
                GPTCLI_VERIFY_FILE,
            )

            km = make_key_manager()
            assert km._salt_path == GPTCLI_SALT_FILE
            assert km._key_path == GPTCLI_KEY_CACHE_FILE
            assert km._verify_path == GPTCLI_VERIFY_FILE
            assert km._params_path == GPTCLI_KDF_PARAMS_FILE
