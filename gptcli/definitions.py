"""This file holds common definitions/constants used throughout the project"""

import os

PROJECT_ROOT_DIRECTORY: str = os.getcwd()

GPTCLI_STORAGE_FILEPATH: str = os.path.expanduser("~/.gptcli/storage")
GPTCLI_KEYS_OPENAI: str = os.path.expanduser("~/.gptcli/keys/openai")
OPENAI_API_KEY: str = "OPENAI_API_KEY"
