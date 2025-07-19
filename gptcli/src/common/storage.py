"""Will handle access and storage of messages"""

import json
import logging
from datetime import datetime, timezone
from glob import glob
from logging import Logger
from os import path
from time import time
from typing import Any

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR,
)
from gptcli.src.common.constants import GRN, MGA, MISTRAL, OPENAI, RST
from gptcli.src.common.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


supported_storage_types = ["json", "db"]


class Storage:
    """The basic representation of storage."""

    def __init__(self, provider: str) -> None:
        self._provider: str = provider

        self._json_dir: str = ""
        if self._provider == MISTRAL:
            self._json_dir = GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR
        elif self._provider == OPENAI:
            self._json_dir = GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

    def store_messages(self, messages: Messages) -> None:
        """Stores Messages objects to ~/.gptcli/storage/

        Args:
            messages (Messages): A Messages object holds Message objects.
        """
        logger.info("Storing Messages to local filesystem.")
        if len(messages) > 0:
            filepath = self._create_json_filepath()
            with open(filepath, "w", encoding="utf8") as fp:
                fp.write(messages.to_json())

    def _create_json_filepath(self) -> str:
        epoch: str = str(int(time()))
        datetime_now_utc: str = datetime.now(tz=timezone.utc).strftime(r"_%Y_%m_%d__%H_%M_%S_")
        filename: str = "_".join([epoch, datetime_now_utc, "chat"]) + ".json"
        filepath: str = path.join(self._json_dir, filename)
        return filepath

    def extract_messages(self) -> Messages:
        logger.info("Extracting messages from storage.")
        filepaths: list[str] = glob(path.expanduser(path.join(self._json_dir, "*.json")))
        last_chat_session: str = max(filepaths, key=path.getctime)

        file_contents_messages: list[dict[str, Any]] = []
        with open(last_chat_session, "r", encoding="utf8") as fp:
            file_contents_messages = json.load(fp)["messages"]

        messages: Messages = Messages()
        for message in file_contents_messages:
            m: Message = MessageFactory.message_from_dict(message=message)
            messages.add(message=m)

        return messages

    def show_messages(self) -> None:
        messages: Messages = self.extract_messages()
        for message in messages:
            if message.is_reply:
                print_formatted_text(ANSI(f"{MGA}>>>{RST} " + message.content))
            else:
                print_formatted_text(ANSI(f"{GRN}>>>{RST} " + message.content))
