"""Use this to install or configure the local machine environment."""

import logging
import os
from logging import Logger

from gptcli.constants import (
    GPTCLI_INSTALL_SUCCESSFUL,
    GPTCLI_KEYS_FILEPATH,
    GPTCLI_KEYS_OPENAI,
    GPTCLI_ROOT_FILEPATH,
    GPTCLI_STORAGE_FILEPATH,
    OPENAI_API_KEY,
)
from gptcli.src.common.api.openai import SingleExchange
from gptcli.src.common.constants import openai
from gptcli.src.common.message import Message, MessageFactory, Messages
from gptcli.src.modes.chat import ChatInstall

logger: Logger = logging.getLogger(__name__)


class Install:
    """Class to hold all the install tools for the local machine"""

    def standard_install(self) -> None:
        """Performs standard install by creating local file directory with needed config files"""
        logger.info("Performing standard install.")
        if not self._is_installed():
            self._create_folder_structure()
            openai_api_key = self._setup_api_key()
            self._write_api_key_to_openai_file(openai_api_key=openai_api_key)
            self._load_api_key_to_environment_variable()
            self._mark_install_as_successful()
        else:
            logger.info("GPTCLI already installed.")

    def _is_installed(self) -> bool:
        logger.info("Checking if GPTCLI is installed.")
        is_installed = False
        try:
            with open(GPTCLI_INSTALL_SUCCESSFUL, "r", encoding="utf8"):
                is_installed = True
        except FileNotFoundError:
            logger.exception("FileNotFoundError: install marker not found")

        return is_installed

    def _create_folder_structure(self) -> None:
        if not self._is_gptcli_folder_present():
            logger.info("Creating basic folder structure.")
            os.mkdir(GPTCLI_ROOT_FILEPATH)
            os.mkdir(GPTCLI_STORAGE_FILEPATH)
            os.mkdir(GPTCLI_KEYS_FILEPATH)
            with open(GPTCLI_KEYS_OPENAI, "w", encoding="utf8"):
                pass  # no need to do anything as file was created
        else:
            logger.info(".gptcli config folder is already present")

    def _is_gptcli_folder_present(self) -> bool:
        logger.info("Checking for .gptcli")
        is_present = os.path.exists(GPTCLI_ROOT_FILEPATH)

        return is_present

    def _setup_api_key(self) -> str:
        logger.info("Asking user for OpenAI API key.")
        chat: ChatInstall = ChatInstall()
        openai_api_key: str = ""
        while True:
            openai_api_key = chat.prompt("Enter your OpenAI API key: ")
            if self._is_valid_openai_api_key(openai_api_key):
                logger.info("Valid API key detected.")
                break
            else:
                print("Invalid OpenAI API key detected...")
        return openai_api_key

    def _write_api_key_to_openai_file(self, openai_api_key: str) -> None:
        logger.info("Loading API key to OpenAI file.")
        if self._is_openai_file_present():
            file_permissions = 0o600
            with open(GPTCLI_KEYS_OPENAI, "w", encoding="utf8", newline="") as filepointer:
                os.chmod(GPTCLI_KEYS_OPENAI, file_permissions)
                filepointer.write(openai_api_key)
        else:
            logger.info("Failed to load API key to OpenAI file")

    def _is_openai_file_present(self) -> bool:
        logger.info("Checking for '.gptcli/keys/OpenAI'.")
        is_present = False
        try:
            with open(GPTCLI_KEYS_OPENAI, "r", encoding="utf8"):
                is_present = True
        except FileNotFoundError:
            is_present = False

        return is_present

    def _load_api_key_to_environment_variable(self) -> None:
        logger.info("Loading API key to environment variable.")
        api_key = os.getenv(OPENAI_API_KEY)
        if api_key is None:
            with open(GPTCLI_KEYS_OPENAI, "r", encoding="utf8") as filepointer:
                os.environ[OPENAI_API_KEY] = filepointer.readline()
        else:
            logger.info("API key already loaded")

    def _is_valid_openai_api_key(self, key: str) -> bool:
        logger.info("Checking if OpenAI API key is valid.")
        message: Message = MessageFactory.create_user_message(role="user", content="Hi!", model=openai["O4_MINI"])
        messages: Messages = Messages()
        messages.add_message(message)
        is_valid = SingleExchange(model=openai["O4_MINI"], messages=messages).is_valid_api_key(key)

        return is_valid

    def _mark_install_as_successful(self) -> None:
        logger.info("Marking install as successful.")
        with open(GPTCLI_INSTALL_SUCCESSFUL, "w", encoding="utf8"):
            pass  # simply create the file
