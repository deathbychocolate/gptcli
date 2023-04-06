"""
Use this to install or configure the local machine environment
"""
import os
import logging

import requests


class Install:
    """Class to hold all the install tools for the local machine"""

    def __init__(self) -> None:
        self.home_directory = os.path.expanduser("~")
        self.gptcli_filepath = "/".join([self.home_directory, ".gptcli"])
        self.keys_filepath = "/".join([self.gptcli_filepath, "keys"])
        self.openai_filepath = "/".join([self.keys_filepath, "openai"])

    def is_gptcli_folder_present(self) -> bool:
        """Checks to see if the .gptcli is present in the home directory"""

        logging.info("Checking for .gptcli")
        is_present = os.path.exists(self.gptcli_filepath)

        return is_present

    def is_keys_folder_present(self) -> bool:
        """Checks to see if the keys folder is present under the .gptcli folder"""

        logging.info("Checking for .gptcli/keys")
        is_present = os.path.exists(self.keys_filepath)

        return is_present

    def is_openai_file_present(self) -> bool:
        """Checks to see if the openai file is present under the .gptcli/keys folder"""

        logging.info("Checking for .gptcli/keys/openai")
        is_present = False
        try:
            with open(self.openai_filepath, "r", encoding="utf8"):
                is_present = True
        except FileNotFoundError:
            is_present = False

        return is_present

    def openai_contains_one_line(self) -> bool:
        """Checks to see if the file openai contains one line"""

        logging.info("Checking if openai has one line")
        contains_one_line = False
        with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
            lines = filepointer.readlines()
            if len(lines) == 1:
                contains_one_line = True

        return contains_one_line

    def is_openai_file_populated_with_a_valid_api_key(self) -> bool:
        """Checks if API key is valid by performing a cheap (100 token) chat completion.
        to https://api.openai.com/v1/completions"""

        request_url = "https://api.openai.com/v1/completions"
        request_headers = {
            "Accept": "text/event-stream",
            "Authorization": " ".join(["Bearer", os.getenv("OPENAI_API_KEY")]),
        }
        request_body = {
            "model": "text-davinci-003",
            "prompt": "Hi!",
            "max_tokens": 100,
            "temperature": 0,
            "stream": True,
        }

        is_valid_api_key = False
        try:
            requests.post(
                request_url,
                stream=True,
                headers=request_headers,
                json=request_body,
                timeout=3,  # seconds
            )
            is_valid_api_key = True
        except TimeoutError:
            is_valid_api_key = False

        return is_valid_api_key

    def load_api_key_to_environment_variable(self) -> None:
        """Loads API key to environment variable OPENAI_API_KEY"""

        logging.info("Loading API key to environment variable")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.readline()
        else:
            logging.warning("API key already loaded")
