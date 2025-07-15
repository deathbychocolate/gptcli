"""Use this to install or configure the local machine environment."""

import logging
import os
from logging import Logger

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_MISTRAL_KEYS_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR,
    GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEYS_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR,
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
