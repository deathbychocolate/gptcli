"""
Use this to install or configure the local machine environment
"""
import os
import logging

from src.main.api_helper import OpenAIHelper
from src.main.chat import ChatInstall

logger = logging.getLogger(__name__)


class Install:
    """Class to hold all the install tools for the local machine"""

    def __init__(self, openai_api_key="", random_id="") -> None:
        self.openai_api_key = openai_api_key
        self.random_id = random_id
        self.home_directory = os.path.expanduser("~")
        self.gptcli_filepath = os.path.join(self.home_directory, f".gptcli{self.random_id}")
        self.install_successful_filepath = os.path.join(self.gptcli_filepath, ".install_successful")
        self.messages_filepath = os.path.join(self.gptcli_filepath, "messages")
        self.keys_filepath = os.path.join(self.gptcli_filepath, "keys")
        self.openai_filepath = os.path.join(self.keys_filepath, "openai")

    def standard_install(self) -> None:
        """Performs standard install by creating local file directory with needed config files"""
        logger.info("Performing standard install")
        if not self._is_installed():
            if not self._is_gptcli_folder_present():
                self._create_folder_structure()
            if not self._is_openai_file_populated_with_a_valid_api_key():
                self._setup_api_key()
                self._write_api_key_to_openai_file()
            if os.getenv("OPENAI_API_KEY") is None:
                self._load_api_key_to_environment_variable()
            self._mark_install_as_successful()
        else:
            logger.info("GPTCLI already installed")

    def _is_installed(self) -> bool:
        logger.info("Checking if GPTCLI is installed")
        is_installed = False
        try:
            with open(self.install_successful_filepath, "r", encoding="utf8"):
                is_installed = True
        except FileNotFoundError:
            logger.exception("FileNotFoundError: install marker not found")

        return is_installed

    def _create_folder_structure(self) -> None:
        if not self._is_gptcli_folder_present():
            logger.info("Creating basic folder structure")
            os.mkdir(self.gptcli_filepath)
            os.mkdir(self.messages_filepath)
            os.mkdir(self.keys_filepath)
            with open(self.openai_filepath, "w", encoding="utf8"):
                pass  # no need to do anything as file was created
        else:
            logger.info(".gptcli config folder is already present")

    def _is_gptcli_folder_present(self) -> bool:
        logger.info("Checking for .gptcli")
        is_present = os.path.exists(self.gptcli_filepath)

        return is_present

    def _setup_api_key(self) -> None:
        logger.info("Asking user for openai API key")
        chat = ChatInstall()
        while True:
            self.openai_api_key = chat.prompt(">>> [GPTCLI]: Enter your openai API key: ")
            if self._is_valid_openai_api_key(self.openai_api_key):
                logger.info("Valid API key detected")
                break
            else:
                print(">>> [GPTCLI]: Invalid openai API key detected...")

    def _write_api_key_to_openai_file(self) -> None:
        logger.info("Loading API key to openai file")
        if self._is_openai_file_present():
            with open(self.openai_filepath, "w", encoding="utf8", newline="") as filepointer:
                filepointer.write(self.openai_api_key)
        else:
            logger.info("Failed to load API key to openai file")

    def _load_api_key_to_environment_variable(self) -> None:
        logger.info("Loading API key to environment variable")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.readline()
        else:
            logger.info("API key already loaded")

    def _is_openai_file_present(self) -> bool:
        logger.info("Checking for .gptcli/keys/openai")
        is_present = False
        try:
            with open(self.openai_filepath, "r", encoding="utf8"):
                is_present = True
        except FileNotFoundError:
            is_present = False

        return is_present

    def _is_openai_file_populated_with_a_valid_api_key(self) -> bool:
        logger.info("Checking if openai file contains valid API key")
        key = None
        with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
            key = filepointer.readline()
        is_valid_api_key = self._is_valid_openai_api_key(key)

        return is_valid_api_key

    def _is_valid_openai_api_key(self, key: str) -> bool:
        logger.info("Checking if openai API key is valid")
        is_valid = OpenAIHelper(model=OpenAIHelper.GPT_3_5, user_input="Hi!").is_valid_api_key(key)

        return is_valid

    def _mark_install_as_successful(self) -> None:
        logger.info("Marking install as successful")
        with open(self.install_successful_filepath, "w", encoding="utf8") as filepointer:
            pass  # simply create the file
