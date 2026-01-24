"""This file holds common definitions/constants used throughout the project"""

import os

PROJECT_ROOT_DIRECTORY: str = os.getcwd()

# Common
GPTCLI_ROOT_FILEPATH: str = os.path.expanduser("~/.gptcli")


# OpenAI
GPTCLI_PROVIDER_OPENAI: str = os.path.join(GPTCLI_ROOT_FILEPATH, "openai")
GPTCLI_PROVIDER_OPENAI_INSTALL_SUCCESSFUL_FILE: str = os.path.join(GPTCLI_PROVIDER_OPENAI, ".install_successful")
GPTCLI_PROVIDER_OPENAI_STORAGE_DIR: str = os.path.join(GPTCLI_PROVIDER_OPENAI, "storage")
GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR: str = os.path.join(GPTCLI_PROVIDER_OPENAI_STORAGE_DIR, "json")
GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR: str = os.path.join(GPTCLI_PROVIDER_OPENAI_STORAGE_DIR, "ocr")
GPTCLI_PROVIDER_OPENAI_STORAGE_DB_DIR: str = os.path.join(GPTCLI_PROVIDER_OPENAI_STORAGE_DIR, "db")
GPTCLI_PROVIDER_OPENAI_KEYS_DIR: str = os.path.join(GPTCLI_PROVIDER_OPENAI, "keys")
GPTCLI_PROVIDER_OPENAI_KEY_FILE: str = os.path.join(GPTCLI_PROVIDER_OPENAI_KEYS_DIR, "main")

OPENAI_API_KEY: str = "DBC_GPTCLI_OPENAI_API_KEY"  # The key we use to search in os.environ.
OPENAI_ENDPOINT_CHAT_COMPLETIONS: str = "https://api.openai.com/v1/chat/completions"


# Mistral
GPTCLI_PROVIDER_MISTRAL: str = os.path.join(GPTCLI_ROOT_FILEPATH, "mistral")
GPTCLI_PROVIDER_MISTRAL_INSTALL_SUCCESSFUL_FILE: str = os.path.join(GPTCLI_PROVIDER_MISTRAL, ".install_successful")
GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR: str = os.path.join(GPTCLI_PROVIDER_MISTRAL, "storage")
GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR: str = os.path.join(GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR, "json")
GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR: str = os.path.join(GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR, "ocr")
GPTCLI_PROVIDER_MISTRAL_STORAGE_DB_DIR: str = os.path.join(GPTCLI_PROVIDER_MISTRAL_STORAGE_DIR, "db")
GPTCLI_PROVIDER_MISTRAL_KEYS_DIR: str = os.path.join(GPTCLI_PROVIDER_MISTRAL, "keys")
GPTCLI_PROVIDER_MISTRAL_KEY_FILE: str = os.path.join(GPTCLI_PROVIDER_MISTRAL_KEYS_DIR, "main")

MISTRAL_API_KEY: str = "DBC_GPTCLI_MISTRAL_API_KEY"  # The key we use to search in os.environ.
MISTRAL_ENDPOINT_CHAT_COMPLETIONS: str = "https://api.mistral.ai/v1/chat/completions"


# Legacy (up to version 0.20.2)
GPTCLI_LEGACY_INSTALL_SUCCESSFUL: str = os.path.join(GPTCLI_ROOT_FILEPATH, ".install_successful")
GPTCLI_LEGACY_KEYS: str = os.path.join(GPTCLI_ROOT_FILEPATH, "keys")
GPTCLI_LEGACY_API_KEY: str = os.path.join(GPTCLI_LEGACY_KEYS, "openai")
GPTCLI_LEGACY_STORAGE: str = os.path.join(GPTCLI_ROOT_FILEPATH, "storage")
