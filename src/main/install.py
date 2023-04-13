"""
Use this to install or configure the local machine environment
"""
import os
import logging

import requests

logger = logging.getLogger(__name__)


class Install:
    """Class to hold all the install tools for the local machine"""

    def __init__(self, openai_api_key="", random_id="") -> None:
        self.openai_api_key = openai_api_key
        self.random_id = random_id
        self.home_directory = os.path.expanduser("~")
        self.gptcli_filepath = os.path.join(self.home_directory, f".gptcli{self.random_id}")
        self.messages_filepath = os.path.join(self.gptcli_filepath, "messages")
        self.keys_filepath = os.path.join(self.gptcli_filepath, "keys")
        self.openai_filepath = os.path.join(self.keys_filepath, "openai")

    def standard_install(self) -> None:
        """Performs standard install by creating local file directory with needed config files"""
        if not self._is_gptcli_folder_present():
            self._create_folders()
            self._ask_for_api_key()
            self._load_api_key_to_openai_file()
        else:
            logger.info("Application already installed")

        self._load_api_key_to_environment_variable()

    def _create_folders(self) -> None:
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

    def _ask_for_api_key(self) -> None:
        logger.info("Asking user for openai API key")
        if self._is_openai_file_present() and self._is_not_openai_file_populated_with_a_valid_api_key():
            while True:
                print(">>> Invalid openai api key detected...")
                key = str(input(">>> Enter your openai API key: "))
                self.openai_api_key = key
                if self._is_valid_openai_api_key(self.openai_api_key):
                    logger.info("Valid API key detected")
                    break
        else:
            logger.info("Not asking for API key as openai file is missing or the API is valid")

    def _load_api_key_to_openai_file(self) -> None:
        logger.info("Loading API key to openai file")
        if self._is_openai_file_present() and self._is_not_openai_file_populated_with_a_valid_api_key():
            with open(self.openai_filepath, "w", encoding="utf8", newline="") as filepointer:
                filepointer.write(self.openai_api_key)
        else:
            logger.info("Failed to load api key to openai file")

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

    def _is_not_openai_file_populated_with_a_valid_api_key(self) -> bool:
        is_not_valid_api_key = not self._is_openai_file_populated_with_a_valid_api_key()
        return is_not_valid_api_key

    def _is_openai_file_populated_with_a_valid_api_key(self) -> bool:
        logger.info("Checking if openai file contains valid API key")
        key = None
        with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
            key = filepointer.readline()
        is_valid_api_key = self._is_valid_openai_api_key(key)

        return is_valid_api_key

    def _is_valid_openai_api_key(self, key: str) -> bool:
        logger.info("Checking if openai api key is valid")
        request_url = "https://api.openai.com/v1/chat/completions"
        request_headers = {
            "Accept": "text/event-stream",
            "Authorization": " ".join(["Bearer", key]),
        }
        request_body = {
            "model": "gpt-3.5-turbo",
            "max_tokens": 10,
            "temperature": 0,
            "stream": True,
            "messages": [{"role": "user", "content": "hi!"}],
        }

        is_valid_api_key = False
        try:
            response = requests.post(
                request_url,
                stream=True,
                headers=request_headers,
                json=request_body,
                timeout=3,  # seconds
            )
        except TimeoutError as error:
            logger.exception(error)

        if response.status_code == 200:
            logger.info("API key is valid")
            is_valid_api_key = True

        return is_valid_api_key
