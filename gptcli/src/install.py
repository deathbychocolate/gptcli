"""Use this to install or configure the local machine environment."""

import logging
import os
from logging import Logger

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEYS_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
    GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEYS_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR,
)
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
from gptcli.src.modes.chat import ChatInstall

logger: Logger = logging.getLogger(__name__)

MESSAGE_FACTORY_MISTRAL: MessageFactory = MessageFactory(provider=ProviderNames.MISTRAL.value)
MESSAGE_FACTORY_OPENAI: MessageFactory = MessageFactory(provider=ProviderNames.OPENAI.value)


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

        encryption: Encryption | None = get_or_initialize_encryption(no_cache=self._no_cache)
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
