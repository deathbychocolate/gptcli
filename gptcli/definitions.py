"""This file holds common definitions/constants used throughout the project"""

import os

PROJECT_ROOT_DIRECTORY: str = os.getcwd()

GPTCLI_ROOT_FILEPATH: str = os.path.expanduser("~/.gptcli")
GPTCLI_INSTALL_SUCCESSFUL: str = os.path.join(GPTCLI_ROOT_FILEPATH, ".install_successful")
GPTCLI_STORAGE_FILEPATH: str = os.path.join(GPTCLI_ROOT_FILEPATH, "storage")
GPTCLI_KEYS_FILEPATH: str = os.path.join(GPTCLI_ROOT_FILEPATH, "keys")
GPTCLI_KEYS_OPENAI: str = os.path.join(GPTCLI_ROOT_FILEPATH, "keys/openai")
OPENAI_API_KEY: str = "<YOUR_OPENAI_API_KEY>"
