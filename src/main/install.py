"""
Use this to install or configure the local machine environment
"""
import os
import logging

import requests


class Install:
    """Class to hold all the install tools for the local machine"""

    def __init__(self, openai_api_key=None, random_id="") -> None:
        self.openai_api_key = openai_api_key
        self.random_id = random_id
        self.home_directory = os.path.expanduser("~")
        self.gptcli_filepath = os.path.join(self.home_directory, f".gptcli_{self.random_id}")
        self.keys_filepath = os.path.join(self.gptcli_filepath, "keys")
        self.openai_filepath = os.path.join(self.keys_filepath, "openai")

    def _create_folders(self) -> None:
        logging.info("Creating basic folder structure")
        os.mkdir(self.gptcli_filepath)
        os.mkdir(self.keys_filepath)
        with open(self.openai_filepath, "w", encoding="utf8"):
            pass  # no need to do anything as file was created

    def _is_gptcli_folder_present(self) -> bool:
        logging.info("Checking for .gptcli")
        is_present = os.path.exists(self.gptcli_filepath)

        return is_present

    def _is_keys_folder_present(self) -> bool:
        logging.info("Checking for .gptcli/keys")
        is_present = os.path.exists(self.keys_filepath)

        return is_present

    def _is_openai_file_present(self) -> bool:
        logging.info("Checking for .gptcli/keys/openai")
        is_present = False
        try:
            with open(self.openai_filepath, "r", encoding="utf8"):
                is_present = True
        except FileNotFoundError:
            is_present = False

        return is_present

    def _openai_contains_one_line(self) -> bool:
        logging.info("Checking if openai has one line")
        contains_one_line = False
        with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
            lines = filepointer.readlines()
            if len(lines) == 1:
                contains_one_line = True

        return contains_one_line

    def _is_openai_file_populated_with_a_valid_api_key(self) -> bool:
        request_url = "https://api.openai.com/v1/completions"
        request_headers = {
            "Accept": "text/event-stream",
            "Authorization": " ".join(["Bearer", os.getenv("OPENAI_API_KEY")]),
        }
        request_body = {
            "model": "gpt-3.5-turbo",
            "prompt": "Hi!",
            "max_tokens": 10,
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

    def _load_api_key_to_openai_file(self) -> None:
        logging.info("Loading API key to openai file")
        key = self.openai_api_key
        filepath = self.openai_filepath
        with open(filepath, "w", encoding="utf8", newline="") as filepointer:
            filepointer.write(key)

    def _load_api_key_to_environment_variable(self) -> None:
        logging.info("Loading API key to environment variable")
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            with open(self.openai_filepath, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.readline()
        else:
            logging.warning("API key already loaded")
