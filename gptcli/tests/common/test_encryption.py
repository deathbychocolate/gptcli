"""Holds all the tests for encryption.py."""

import os

import pytest

from gptcli.src.common.encryption import (
    _NONCE_SIZE,
    _SALT_SIZE,
    _TAG_SIZE,
    Encryption,
)


class TestEncryption:

    class TestInit:

        def test_accepts_32_byte_key(self) -> None:
            key = os.urandom(32)
            enc = Encryption(key=key)
            assert enc is not None

        def test_raises_on_invalid_key_length(self) -> None:
            with pytest.raises(ValueError):
                Encryption(key=os.urandom(16))

    class TestEncrypt:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_returns_bytes(self, encryption: Encryption) -> None:
            result = encryption.encrypt(b"hello")
            assert isinstance(result, bytes)

        def test_output_is_different_from_input(self, encryption: Encryption) -> None:
            plaintext = b"hello world"
            ciphertext = encryption.encrypt(plaintext)
            assert ciphertext != plaintext

        def test_output_length_is_input_plus_28_bytes(self, encryption: Encryption) -> None:
            plaintext = b"test data here"
            ciphertext = encryption.encrypt(plaintext)
            assert len(ciphertext) == len(plaintext) + _NONCE_SIZE + _TAG_SIZE

        def test_encrypting_same_plaintext_twice_produces_different_ciphertext(self, encryption: Encryption) -> None:
            plaintext = b"same input"
            c1 = encryption.encrypt(plaintext)
            c2 = encryption.encrypt(plaintext)
            assert c1 != c2

        def test_encrypts_empty_bytes(self, encryption: Encryption) -> None:
            result = encryption.encrypt(b"")
            assert isinstance(result, bytes)
            assert len(result) == _NONCE_SIZE + _TAG_SIZE

    class TestHasEncryptedContent:

        def test_returns_true_for_minimum_valid_length(self) -> None:
            data = os.urandom(_NONCE_SIZE + _TAG_SIZE)
            assert Encryption._has_encrypted_content(data) is True

        def test_returns_true_for_longer_than_minimum(self) -> None:
            data = os.urandom(_NONCE_SIZE + _TAG_SIZE + 100)
            assert Encryption._has_encrypted_content(data) is True

        def test_returns_false_for_empty_bytes(self) -> None:
            assert Encryption._has_encrypted_content(b"") is False

        def test_returns_false_for_one_byte_below_minimum(self) -> None:
            data = os.urandom(_NONCE_SIZE + _TAG_SIZE - 1)
            assert Encryption._has_encrypted_content(data) is False

    class TestDecrypt:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_roundtrip_returns_original_plaintext(self, encryption: Encryption) -> None:
            plaintext = b"hello world"
            ciphertext = encryption.encrypt(plaintext)
            assert encryption.decrypt(ciphertext) == plaintext

        def test_roundtrip_with_unicode_content(self, encryption: Encryption) -> None:
            plaintext = "Héllo wörld 文档 Кириллица".encode("utf-8")
            ciphertext = encryption.encrypt(plaintext)
            assert encryption.decrypt(ciphertext) == plaintext

        def test_roundtrip_with_binary_content(self, encryption: Encryption) -> None:
            plaintext = bytes(range(256))
            ciphertext = encryption.encrypt(plaintext)
            assert encryption.decrypt(ciphertext) == plaintext

        def test_roundtrip_with_empty_bytes(self, encryption: Encryption) -> None:
            ciphertext = encryption.encrypt(b"")
            assert encryption.decrypt(ciphertext) == b""

        def test_returns_none_on_tampered_ciphertext(self, encryption: Encryption) -> None:
            ciphertext = encryption.encrypt(b"secret")
            tampered = ciphertext[:20] + bytes([ciphertext[20] ^ 0xFF]) + ciphertext[21:]
            assert encryption.decrypt(tampered) is None

        def test_returns_none_on_wrong_key(self) -> None:
            enc1 = Encryption(key=os.urandom(32))
            enc2 = Encryption(key=os.urandom(32))
            ciphertext = enc1.encrypt(b"secret")
            assert enc2.decrypt(ciphertext) is None

        def test_returns_none_on_truncated_ciphertext(self, encryption: Encryption) -> None:
            assert encryption.decrypt(b"too short") is None

    class TestEncryptFile:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_creates_enc_file(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(b"hello")
            encryption.encrypt_file(filepath)
            assert os.path.exists(filepath + ".enc")

        def test_removes_original_file(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(b"hello")
            encryption.encrypt_file(filepath)
            assert not os.path.exists(filepath)

        def test_enc_file_content_differs_from_original(self, encryption: Encryption, tmp_path: str) -> None:
            original_content = b"hello world"
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(original_content)
            encryption.encrypt_file(filepath)
            with open(filepath + ".enc", "rb") as f:
                enc_content = f.read()
            assert enc_content != original_content

        def test_raises_on_nonexistent_file(self, encryption: Encryption) -> None:
            with pytest.raises(FileNotFoundError):
                encryption.encrypt_file("/nonexistent/path/file.txt")

    class TestDecryptFile:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        def test_returns_original_content(self, encryption: Encryption, tmp_path: str) -> None:
            original_content = b"hello world"
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(original_content)
            encryption.encrypt_file(filepath)
            result = encryption.decrypt_file(filepath + ".enc")
            assert result == original_content

        def test_does_not_write_to_disk(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(b"hello")
            encryption.encrypt_file(filepath)
            encryption.decrypt_file(filepath + ".enc")
            assert not os.path.exists(filepath)

        def test_returns_none_on_nonexistent_file(self, encryption: Encryption) -> None:
            assert encryption.decrypt_file("/nonexistent/path/file.txt.enc") is None

        def test_returns_none_on_non_enc_extension(self, encryption: Encryption, tmp_path: str) -> None:
            filepath = os.path.join(str(tmp_path), "test.txt")
            with open(filepath, "wb") as f:
                f.write(b"hello")
            assert encryption.decrypt_file(filepath) is None

    class TestGenerateSalt:

        def test_returns_salt_size_bytes(self) -> None:
            salt = Encryption.generate_salt()
            assert len(salt) == _SALT_SIZE

        def test_consecutive_calls_produce_different_salts(self) -> None:
            salt1 = Encryption.generate_salt()
            salt2 = Encryption.generate_salt()
            assert salt1 != salt2

    class TestDeriveKey:

        def test_returns_32_bytes(self) -> None:
            salt = Encryption.generate_salt()
            key = Encryption.derive_key("passphrase", salt)
            assert len(key) == 32

        def test_same_passphrase_and_salt_produce_same_key(self) -> None:
            salt = Encryption.generate_salt()
            key1 = Encryption.derive_key("passphrase", salt)
            key2 = Encryption.derive_key("passphrase", salt)
            assert key1 == key2

        def test_different_passphrase_produces_different_key(self) -> None:
            salt = Encryption.generate_salt()
            key1 = Encryption.derive_key("passphrase1", salt)
            key2 = Encryption.derive_key("passphrase2", salt)
            assert key1 != key2

        def test_different_salt_produces_different_key(self) -> None:
            salt1 = Encryption.generate_salt()
            salt2 = Encryption.generate_salt()
            key1 = Encryption.derive_key("passphrase", salt1)
            key2 = Encryption.derive_key("passphrase", salt2)
            assert key1 != key2

    class TestCreateVerificationToken:

        def test_returns_bytes(self) -> None:
            key = os.urandom(32)
            token = Encryption.create_verification_token(key)
            assert isinstance(token, bytes)

    class TestVerifyKey:

        def test_correct_key_returns_true(self) -> None:
            key = os.urandom(32)
            token = Encryption.create_verification_token(key)
            assert Encryption.verify_key(key, token) is True

        def test_wrong_key_returns_false(self) -> None:
            key1 = os.urandom(32)
            key2 = os.urandom(32)
            token = Encryption.create_verification_token(key1)
            assert Encryption.verify_key(key2, token) is False
