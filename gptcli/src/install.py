"""Use this to install or configure the local machine environment."""

import json
import logging
import os
import re
import uuid
from glob import glob
from logging import Logger
from typing import Any

from gptcli.constants import (
    GPTCLI_LEGACY_API_KEY,
    GPTCLI_LEGACY_INSTALL_SUCCESSFUL,
    GPTCLI_LEGACY_KEYS,
    GPTCLI_LEGACY_STORAGE,
    GPTCLI_MANIFEST_FILENAME,
    GPTCLI_METADATA_FILENAME,
    GPTCLI_PROVIDER_MISTRAL,
    GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEYS_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_LEGACY_JSON_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
    GPTCLI_PROVIDER_OPENAI,
    GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEYS_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_LEGACY_JSON_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR,
    GPTCLI_SESSION_FILENAME,
)
from gptcli.src.commands.encryption_commands import EncryptionCommands
from gptcli.src.common.api import SingleExchange
from gptcli.src.common.constants import (
    MISTRAL,
    OPENAI,
    MistralModelsChat,
    MistralUserRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    ProviderNames,
)
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.key_management import KeyManager, make_key_manager
from gptcli.src.common.message import Message, MessageFactory, Messages
from gptcli.src.common.passphrase import PassphrasePrompt
from gptcli.src.common.storage import Storage
from gptcli.src.modes.chat import ChatInstall

logger: Logger = logging.getLogger(__name__)

MESSAGE_FACTORY_MISTRAL: MessageFactory = MessageFactory(provider=ProviderNames.MISTRAL.value)
MESSAGE_FACTORY_OPENAI: MessageFactory = MessageFactory(provider=ProviderNames.OPENAI.value)

_EPOCH_TIMESTAMP_PATTERN: re.Pattern[str] = re.compile(r"^(\d+)_")


class Migrate:

    @staticmethod
    def get_or_initialize_encryption(no_cache: bool = False) -> Encryption | None:
        """Get or initialize encryption for the installation.

        If encryption is already initialized, loads the existing key.
        Otherwise, prompts for a passphrase and initializes encryption.

        Args:
            no_cache (bool): If True, disable encryption key caching.

        Returns:
            Encryption | None: An Encryption instance ready for use, or None if the user aborted.
        """
        km: KeyManager = make_key_manager(no_cache=no_cache)
        if km.is_initialized():
            key: bytes | None = km.load_key()
        else:
            passphrase: str | None = PassphrasePrompt.create_with_confirmation()
            if passphrase is None:
                return None
            key = km.initialize(passphrase)
        if key is None:
            return None
        return Encryption(key=key)

    @staticmethod
    def migrate_legacy_tree() -> bool:
        """Migrates the OpenAI API key and the messages to the new tree structure.

        We do not want to lose the OpenAI key nor the messages in storage.
        To accomplish this, we move them to the new tree structure which supports multiple providers.

        For example, the migration should make ~/.gptcli tree structure change from this:
        .
        ├── .install_successful
        ├── keys
        │   └── openai
        └── storage
            ├── 1733422696__2024_12_05__18_18_16_chat.json
            ├── 1733433483__2024_12_05__21_18_03_chat.json

        To this:
        .
        └── openai
            ├── .install_successful
            ├── keys
            │   └── main
            └── storage
                ├── db
                └── json
                    ├── 1733422696__2024_12_05__18_18_16_chat.json
                    ├── 1733433483__2024_12_05__21_18_03_chat.json

        Returns:
            bool: True if the migration was completed and changes to the tree structure will persist. Otherwise, False.
        """
        logger.info("Checking if setup is Legacy setup and therefore migrate.")
        if Migrate._has_legacy_install_marker():
            logger.info("Setup is Legacy, proceeding with migration.")

            os.makedirs(os.path.dirname(GPTCLI_PROVIDER_OPENAI_KEY_FILE), exist_ok=True)
            os.replace(GPTCLI_LEGACY_API_KEY, GPTCLI_PROVIDER_OPENAI_KEY_FILE)

            target: str = ""
            files: list[str] = [file.split(os.path.sep)[-1] for file in glob(GPTCLI_LEGACY_STORAGE + "/" + "*.json")]
            if len(files) > 0:
                os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_LEGACY_JSON_DIR, exist_ok=True)
                for file in files:
                    target = os.path.join(GPTCLI_PROVIDER_OPENAI_STORAGE_LEGACY_JSON_DIR, file)
                    os.replace(GPTCLI_LEGACY_STORAGE + "/" + file, target)

            # complete the new tree structure
            os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR, exist_ok=True)
            with open(GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE, mode="w", encoding="utf8"):
                pass

            # delete legacy tree structure
            os.remove(GPTCLI_LEGACY_INSTALL_SUCCESSFUL)
            os.removedirs(GPTCLI_LEGACY_STORAGE)
            os.removedirs(GPTCLI_LEGACY_KEYS)

        return True

    @staticmethod
    def to_encrypted(no_cache: bool = False) -> bool:
        """Migrate existing cleartext data to encrypted format.

        Detects if provider data exists without encryption being initialized.
        If so, prompts for a passphrase, initializes encryption, and encrypts
        all existing cleartext files.

        Args:
            no_cache (bool): If True, disable encryption key caching.

        Returns:
            bool: True if migration was performed, False if skipped.
        """
        logger.info("Checking if migration to encrypted storage is needed.")
        km: KeyManager = make_key_manager(no_cache=no_cache)

        if km.is_initialized():
            logger.info("Encryption already initialized. Skipping migration.")
            return False

        # Check if any provider data exists
        provider_dirs: list[str] = []
        for provider_dir in [GPTCLI_PROVIDER_MISTRAL, GPTCLI_PROVIDER_OPENAI]:
            if os.path.isdir(provider_dir):
                provider_dirs.append(provider_dir)

        if not provider_dirs:
            logger.info("No provider data found. Skipping encryption migration.")
            return False

        logger.info("Unencrypted provider data found. Migrating to encrypted storage.")
        print("Encryption at rest is enabled by default to protect your stored data.")
        print("You will now be prompted to create an encryption passphrase.")
        passphrase: str | None = PassphrasePrompt.create_with_confirmation()
        if passphrase is None:
            return False
        key: bytes = km.initialize(passphrase)
        encryption = Encryption(key=key)

        for provider_dir in provider_dirs:
            cmd = EncryptionCommands(provider_dir=provider_dir, encryption=encryption)
            cmd.encrypt_provider()

        return True

    @staticmethod
    def migrate_to_opaque_storage(encryption: Encryption | None = None) -> None:
        """Migrate timestamp-based storage to opaque UUID-based storage.

        Idempotent: safe to call multiple times. For each provider that has
        a storage/ directory, this method:
        1. Renames json/ to chat/ if json/ exists and chat/ does not.
        2. Moves each timestamp-based chat file into a UUID directory with
           session.json + metadata.json, and builds a chat manifest.
        3. Renames each timestamp-based OCR directory to a UUID directory
           and builds an OCR manifest.

        Args:
            encryption (Encryption | None): Encryption instance for reading/writing
                encrypted files during migration. Required when storage is encrypted.
        """
        logger.info("Checking if migration to opaque storage is needed.")
        providers: list[tuple[str, str, str]] = [
            (
                GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
                GPTCLI_PROVIDER_OPENAI_STORAGE_LEGACY_JSON_DIR,
                GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR,
            ),
            (
                GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
                GPTCLI_PROVIDER_MISTRAL_STORAGE_LEGACY_JSON_DIR,
                GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR,
            ),
        ]

        for storage_dir, legacy_json_dir, chat_dir in providers:
            if not os.path.isdir(storage_dir):
                continue

            # Step 1: Rename json/ → chat/
            if os.path.isdir(legacy_json_dir) and not os.path.isdir(chat_dir):
                logger.info(f"Renaming {legacy_json_dir} to {chat_dir}")
                os.rename(legacy_json_dir, chat_dir)

            # Step 2: Migrate chat files
            if os.path.isdir(chat_dir):
                Migrate._migrate_chat_files(chat_dir, encryption)

            # Step 3: Migrate OCR directories
            ocr_dir = os.path.join(storage_dir, "ocr")
            if os.path.isdir(ocr_dir):
                Migrate._migrate_ocr_dirs(ocr_dir, encryption)

    @staticmethod
    def _write_json(filepath: str, data: Any, encryption: Encryption | None) -> None:
        """Write JSON data to a file, encrypting if encryption is active.

        Args:
            filepath (str): The base filepath (without .enc suffix).
            data (Any): The data to serialize as JSON.
            encryption (Encryption | None): Encryption instance, or None for plaintext.
        """
        content = json.dumps(data, ensure_ascii=False)
        if encryption:
            encrypted = encryption.encrypt(content.encode("utf-8"))
            with open(filepath + ".enc", "wb") as fp:
                fp.write(encrypted)
        else:
            with open(filepath, "w", encoding="utf8") as fp:
                fp.write(content)

    @staticmethod
    def _read_json(filepath: str, encryption: Encryption | None) -> Any | None:
        """Read JSON data from a plaintext or encrypted file.

        Prefers the encrypted file when it exists and encryption is available.

        Args:
            filepath (str): The base filepath (without .enc suffix).
            encryption (Encryption | None): Encryption instance, or None for plaintext only.

        Returns:
            Any | None: The deserialized JSON data, or None if the file is absent or unreadable.
        """
        enc_path = filepath + ".enc"
        if os.path.exists(enc_path):
            if encryption is None:
                logger.warning("Encrypted file found but no encryption key provided: %s", enc_path)
                return None
            decrypted = encryption.decrypt_file(enc_path)
            if decrypted is None:
                return None
            return json.loads(decrypted.decode("utf-8"))
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf8") as fp:
                return json.load(fp)
        return None

    @staticmethod
    def _extend_manifest(directory: str, new_entries: list[dict[str, Any]], encryption: Encryption | None) -> None:
        """Read an existing manifest, extend it with new entries, and write it back.

        Args:
            directory (str): The directory containing the manifest file.
            new_entries (list[dict[str, Any]]): New manifest entries to append.
            encryption (Encryption | None): Encryption instance, or None for plaintext.
        """
        manifest_path = os.path.join(directory, GPTCLI_MANIFEST_FILENAME)
        existing = Migrate._read_json(manifest_path, encryption)
        if existing is None:
            existing = []
        existing.extend(new_entries)
        Migrate._write_json(manifest_path, existing, encryption)

    @staticmethod
    def _migrate_chat_files(chat_dir: str, encryption: Encryption | None) -> None:
        """Migrate timestamp-based chat files to UUID directories.

        For each *__chat.json or *__chat.json.enc file in chat_dir, creates
        a UUID directory, moves the file to session.json[.enc], creates
        metadata.json[.enc], and builds the manifest.

        Args:
            chat_dir (str): The chat storage directory.
            encryption (Encryption | None): Encryption instance, or None for plaintext.
        """
        chat_files = glob(os.path.join(chat_dir, "*_chat.json"))
        chat_files += glob(os.path.join(chat_dir, "*_chat.json.enc"))

        if not chat_files:
            return

        manifest_entries: list[dict[str, Any]] = []

        for filepath in chat_files:
            filename = os.path.basename(filepath)
            epoch = Migrate._extract_epoch_from_filename(filename)
            created = float(epoch) if epoch else 0.0

            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(chat_dir, session_uuid)
            os.makedirs(session_dir, exist_ok=True)

            is_encrypted = filename.endswith(".enc")
            target_name = GPTCLI_SESSION_FILENAME + ".enc" if is_encrypted else GPTCLI_SESSION_FILENAME
            target_path = os.path.join(session_dir, target_name)
            os.rename(filepath, target_path)

            metadata = Storage.build_chat_metadata(session_uuid, created, model="", provider="")
            metadata_path = os.path.join(session_dir, GPTCLI_METADATA_FILENAME)

            # If the session is encrypted but encryption=None, metadata.json is written as plaintext.
            # You could encrypt it via `gptcli all encrypt` on the next run.
            Migrate._write_json(metadata_path, metadata, encryption)

            manifest_entries.append({"uuid": session_uuid, "created": created})
            logger.info(f"Migrated chat file '{filename}' to '{session_uuid}/'")

        Migrate._extend_manifest(chat_dir, manifest_entries, encryption)

    @staticmethod
    def _migrate_ocr_dirs(ocr_dir: str, encryption: Encryption | None) -> None:
        """Migrate timestamp-based OCR directories to UUID directories.

        For each *__ocr directory in ocr_dir, reads existing metadata.json
        for the created timestamp, renames to a UUID directory, and builds
        the manifest.

        Args:
            ocr_dir (str): The OCR storage directory.
            encryption (Encryption | None): Encryption instance, or None for plaintext.
        """
        ocr_dirs = glob(os.path.join(ocr_dir, "*_ocr"))
        if not ocr_dirs:
            return

        manifest_entries: list[dict[str, Any]] = []

        for dirpath in ocr_dirs:
            dirname = os.path.basename(dirpath)

            # Try to get created timestamp from existing metadata.json
            created = Migrate._read_ocr_created_from_metadata(dirpath, encryption)
            if created is None:
                epoch = Migrate._extract_epoch_from_filename(dirname)
                created = float(epoch) if epoch else 0.0

            session_uuid = str(uuid.uuid4())
            target_dir = os.path.join(ocr_dir, session_uuid)
            os.rename(dirpath, target_dir)

            # Update metadata.json uuid if it exists
            Migrate._update_ocr_metadata_uuid(target_dir, session_uuid, encryption)

            manifest_entries.append({"uuid": session_uuid, "created": created})
            logger.info(f"Migrated OCR dir '{dirname}' to '{session_uuid}/'")

        Migrate._extend_manifest(ocr_dir, manifest_entries, encryption)

    @staticmethod
    def _extract_epoch_from_filename(filename: str) -> str:
        """Extract the leading epoch timestamp from a filename.

        Args:
            filename (str): A filename starting with an epoch prefix (e.g., '1733422696_...').

        Returns:
            str: The epoch string, or empty string if no match.
        """
        match = _EPOCH_TIMESTAMP_PATTERN.match(filename)
        return match.group(1) if match else ""

    @staticmethod
    def _read_ocr_created_from_metadata(session_dir: str, encryption: Encryption | None) -> float | None:
        """Read the 'created' timestamp from an OCR session's metadata.json[.enc].

        Args:
            session_dir (str): Path to the OCR session directory.
            encryption (Encryption | None): Encryption instance, or None for plaintext only.

        Returns:
            float | None: The created timestamp, or None if metadata is absent or unreadable.
        """
        metadata_path = os.path.join(session_dir, GPTCLI_METADATA_FILENAME)
        data = Migrate._read_json(metadata_path, encryption)
        if data is None:
            return None
        try:
            return float(data["ocr"]["created"])
        except (KeyError, ValueError):
            return None

    @staticmethod
    def _update_ocr_metadata_uuid(session_dir: str, session_uuid: str, encryption: Encryption | None) -> None:
        """Update the UUID in an OCR session's metadata.json[.enc].

        Args:
            session_dir (str): Path to the OCR session directory.
            session_uuid (str): The new UUID to set.
            encryption (Encryption | None): Encryption instance, or None for plaintext.
        """
        metadata_path = os.path.join(session_dir, GPTCLI_METADATA_FILENAME)
        data = Migrate._read_json(metadata_path, encryption)
        if data is None:
            return
        try:
            data["ocr"]["uuid"] = session_uuid
            Migrate._write_json(metadata_path, data, encryption)
        except (KeyError, ValueError) as exc:
            logger.warning("Failed to update OCR metadata UUID in '%s': %s", metadata_path, exc)

    @staticmethod
    def _has_legacy_install_marker() -> bool:
        """Check if the legacy install marker file exists.

        Returns:
            bool: True if the legacy install marker exists, False otherwise.
        """
        logger.info("Checking for legacy install marker.")
        return os.path.exists(GPTCLI_LEGACY_INSTALL_SUCCESSFUL)


class ProviderInstaller:
    """Handles installation for a specific provider.

    Parameterized by provider-specific constants (directories, key file,
    install marker, model/role defaults, and API validation settings).

    Attributes:
        _provider: The provider name enum value.
        _storage_dirs: List of storage directories to create.
        _keys_dir: Directory for API key storage.
        _key_file: Path to the API key file.
        _install_marker: Path to the install-success marker file.
        _no_cache: Whether to disable encryption key caching.
    """

    def __init__(
        self,
        provider: str,
        storage_dirs: list[str],
        keys_dir: str,
        key_file: str,
        install_marker: str,
        api_provider: str,
        default_model: str,
        default_role: str,
        message_factory: MessageFactory,
        no_cache: bool = False,
    ) -> None:
        """Initialize with provider-specific paths and configuration.

        Args:
            provider (str): The provider name (e.g., 'mistral', 'openai').
            storage_dirs (list[str]): List of storage directories to create.
            keys_dir (str): Directory for API key storage.
            key_file (str): Path to the API key file.
            install_marker (str): Path to the install-success marker file.
            api_provider (str): Provider identifier for API calls.
            default_model (str): Default model for API key validation.
            default_role (str): Default user role for API key validation.
            message_factory (MessageFactory): Factory for creating provider-specific messages.
            no_cache (bool): If True, disable encryption key caching.
        """
        self._provider: str = provider
        self._storage_dirs: list[str] = storage_dirs
        self._keys_dir: str = keys_dir
        self._key_file: str = key_file
        self._install_marker: str = install_marker
        self._api_provider: str = api_provider
        self._default_model: str = default_model
        self._default_role: str = default_role
        self._message_factory: MessageFactory = message_factory
        self._no_cache: bool = no_cache

    def install(self) -> None:
        """Create local file directory with needed config files for the provider."""
        logger.info("Performing install for %s.", self._provider)
        if self._is_already_installed():
            return None

        chat: ChatInstall = ChatInstall(provider=self._provider)
        key: str = chat.prompt(">>> ")
        while not self._is_valid_api_key(key=key):
            key = chat.prompt(">>> ")

        for directory in self._storage_dirs:
            os.makedirs(directory, exist_ok=True)
        os.makedirs(self._keys_dir, exist_ok=True)

        encryption: Encryption | None = Migrate.get_or_initialize_encryption(no_cache=self._no_cache)
        if encryption is None:
            return None
        encrypted: bytes = encryption.encrypt(key.encode("utf-8"))
        with open(self._key_file + ".enc", "wb") as fp:
            fp.write(encrypted)

        with open(self._install_marker, "w", encoding="utf8"):
            pass

        return None

    def _is_valid_api_key(self, key: str) -> bool:
        """Check if the provided API key is valid by making a test API call.

        Args:
            key (str): The API key to validate.

        Returns:
            bool: True if the key is valid, False otherwise.
        """
        logger.info("Checking if provided API key is valid.")
        message: Message = self._message_factory.user_message(
            role=self._default_role, content="Hi!", model=self._default_model
        )
        messages: Messages = Messages()
        messages.add(message)
        return SingleExchange(
            provider=self._api_provider, model=self._default_model, messages=messages
        ).is_valid_api_key(key)

    def _is_already_installed(self) -> bool:
        """Check if the provider is already installed.

        Returns:
            bool: True if the install marker file exists, False otherwise.
        """
        logger.info("Checking if %s is already installed.", self._provider)
        return os.path.exists(self._install_marker)


class Mistral(ProviderInstaller):
    """Installation handler for Mistral AI."""

    def __init__(self, no_cache: bool = False) -> None:
        super().__init__(
            provider=ProviderNames.MISTRAL.value,
            storage_dirs=[
                GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
                GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR,
                GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
                GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR,
            ],
            keys_dir=GPTCLI_PROVIDER_MISTRAL_KEYS_DIR,
            key_file=GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
            install_marker=GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE,
            api_provider=MISTRAL,
            default_model=MistralModelsChat.default(),
            default_role=MistralUserRoles.default(),
            message_factory=MESSAGE_FACTORY_MISTRAL,
            no_cache=no_cache,
        )


class Openai(ProviderInstaller):
    """Installation handler for OpenAI."""

    def __init__(self, no_cache: bool = False) -> None:
        super().__init__(
            provider=ProviderNames.OPENAI.value,
            storage_dirs=[
                GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
                GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR,
                GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR,
                GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR,
            ],
            keys_dir=GPTCLI_PROVIDER_OPENAI_KEYS_DIR,
            key_file=GPTCLI_PROVIDER_OPENAI_KEY_FILE,
            install_marker=GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE,
            api_provider=OPENAI,
            default_model=OpenaiModelsChat.default(),
            default_role=OpenaiUserRoles.default(),
            message_factory=MESSAGE_FACTORY_OPENAI,
            no_cache=no_cache,
        )
