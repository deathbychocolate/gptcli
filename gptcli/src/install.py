"""Use this to install or configure the local machine environment."""

import logging
import os
from glob import glob
from logging import Logger

from gptcli.constants import (
    GPTCLI_LEGACY_API_KEY,
    GPTCLI_LEGACY_INSTALL_SUCCESSFUL,
    GPTCLI_LEGACY_KEYS,
    GPTCLI_LEGACY_STORAGE,
    GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEYS_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
    GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEYS_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR,
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
from gptcli.src.common.message import Message, MessageFactory, Messages
from gptcli.src.modes.chat import ChatInstall

logger: Logger = logging.getLogger(__name__)

MESSAGE_FACTORY_MISTRAL: MessageFactory = MessageFactory(provider=ProviderNames.MISTRAL.value)
MESSAGE_FACTORY_OPENAI: MessageFactory = MessageFactory(provider=ProviderNames.OPENAI.value)


class Migrate:

    def __init__(self) -> None:
        pass

    def from__0_20_2__to__latest(self) -> bool:
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
        if self._is_install_successful():
            logger.info("Setup is Legacy, proceeding with migration.")

            os.makedirs(os.path.dirname(GPTCLI_PROVIDER_OPENAI_KEY_FILE), exist_ok=True)
            os.replace(GPTCLI_LEGACY_API_KEY, GPTCLI_PROVIDER_OPENAI_KEY_FILE)

            target: str = ""
            files: list[str] = [file.split(os.path.sep)[-1] for file in glob(GPTCLI_LEGACY_STORAGE + "/" + "*.json")]
            if len(files) > 0:
                os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR, exist_ok=True)
                for file in files:
                    target = os.path.join(GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR, file)
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
    def _is_install_successful() -> bool:
        logger.info("Checking if Mistral setup has been successful.")
        is_installed = False
        try:
            with open(GPTCLI_LEGACY_INSTALL_SUCCESSFUL, "r", encoding="utf8"):
                is_installed = True
        except FileNotFoundError:
            logger.exception("FileNotFoundError: install marker not found")

        return is_installed


class Mistral:
    """Class to hold all the installation tools for the local machine - specific to Mistral AI needs."""

    def install(self) -> None:
        """Creates local file directory with needed config files - specific to Mistral AI needs."""
        logger.info("Performing install for Mistral AI.")
        if self._is_install_successful():
            return None

        chat: ChatInstall = ChatInstall(provider=ProviderNames.MISTRAL.value)
        key: str = chat.prompt(">>> ")
        while not self._is_valid_api_key(key=key):
            key = chat.prompt(">>> ")

        os.makedirs(GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_MISTRAL_KEYS_DIR, exist_ok=True)
        with open(GPTCLI_PROVIDER_MISTRAL_KEY_FILE, "w", encoding="utf8") as fp:
            fp.write(key)
        open(GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE, "w", encoding="utf8").close()

        return None

    @staticmethod
    def _is_valid_api_key(key: str) -> bool:
        logger.info("Checking if provided API key is valid.")
        model: str = MistralModelsChat.default()
        role: str = MistralUserRoles.default()
        message: Message = MESSAGE_FACTORY_MISTRAL.user_message(role=role, content="Hi!", model=model)
        messages: Messages = Messages()
        messages.add(message)
        is_valid = SingleExchange(provider=MISTRAL, model=role, messages=messages).is_valid_api_key(key)

        return is_valid

    @staticmethod
    def _is_install_successful() -> bool:
        logger.info("Checking if Mistral setup has been successful.")
        is_installed = False
        try:
            with open(GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE, "r", encoding="utf8"):
                is_installed = True
        except FileNotFoundError:
            logger.exception("FileNotFoundError: install marker not found")

        return is_installed


class Openai:
    """Class to hold all the installation tools for the local machine - specific to OpenAI needs."""

    def install(self) -> None:
        """Creates local file directory with needed config files - specific to OpenAI needs."""
        logger.info("Performing install for OpenAI.")
        if self._is_install_successful():
            return None

        chat: ChatInstall = ChatInstall(provider=ProviderNames.OPENAI.value)
        key: str = chat.prompt(">>> ")
        while not self._is_valid_api_key(key=key):
            key = chat.prompt(">>> ")

        os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR, exist_ok=True)
        os.makedirs(GPTCLI_PROVIDER_OPENAI_KEYS_DIR, exist_ok=True)
        with open(GPTCLI_PROVIDER_OPENAI_KEY_FILE, "w", encoding="utf8") as fp:
            fp.write(key)
        open(GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE, "w", encoding="utf8").close()

        return None

    @staticmethod
    def _is_valid_api_key(key: str) -> bool:
        logger.info("Checking if provided API key is valid.")
        model: str = OpenaiModelsChat.default()
        role: str = OpenaiUserRoles.default()
        message: Message = MESSAGE_FACTORY_OPENAI.user_message(role=role, content="Hi!", model=model)
        messages: Messages = Messages()
        messages.add(message)
        is_valid = SingleExchange(provider=OPENAI, model=model, messages=messages).is_valid_api_key(key)

        return is_valid

    @staticmethod
    def _is_install_successful() -> bool:
        logger.info("Checking if OpenAI setup has been successful.")
        is_installed = False
        try:
            with open(GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE, "r", encoding="utf8"):
                is_installed = True
        except FileNotFoundError:
            logger.exception("FileNotFoundError: install marker not found")

        return is_installed
