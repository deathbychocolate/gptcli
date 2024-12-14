"""Will handle access and storage of messages"""

import json
import logging
from datetime import datetime, timezone
from glob import glob
from logging import Logger
from os import path
from time import time

from gptcli.definitions import GPTCLI_STORAGE_FILEPATH
from gptcli.src.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


supported_storage_types = set(["chat", "single_exchange", "metadata"])


class Storage:
    """The basic representation of storage."""

    def store_messages(self, messages: Messages, storage_type: str) -> None:
        """Stores Messages objects to ~/.gptcli/storage/

        Args:
            messages (Messages): A Messages object holds Message objects.
            storage_type (str): A string to describe the type of storage we want. See: supported_storage_types.
        """
        logger.info("Storing Messages to local filesystem.")
        if len(messages) > 0:
            filepath = self._generate_filepath(storage_type)
            with open(filepath, "w", encoding="utf8") as filepointer:
                filepointer.write(messages.to_json(indent=4))

    def _generate_filepath(self, storage_type: str) -> str:
        logger.info("Generating filepath for storing a '%s' storage type.", storage_type)
        if storage_type.casefold() not in supported_storage_types:
            raise NotImplementedError(f"The storage type '{storage_type}' is not supported.")

        epoch: str = str(int(time()))
        datetime_now_utc: str = datetime.now(tz=timezone.utc).strftime(r"_%Y_%m_%d__%H_%M_%S")
        filename: str = "_".join([epoch, datetime_now_utc, storage_type]) + ".json"
        filepath: str = path.join(GPTCLI_STORAGE_FILEPATH, filename)

        return filepath

    def extract_messages(self) -> Messages:
        filepaths: list = glob(path.expanduser("~/.gptcli/storage/*.json"))
        last_chat_session: str = max(filepaths, key=path.getctime)

        file_contents: dict = dict()
        with open(last_chat_session, "r", encoding="utf8") as filepointer:
            file_contents = json.load(filepointer)

        messages: Messages = Messages()
        for message in file_contents["messages"]:
            m: Message = MessageFactory.create_message_from_dict(message=message)
            messages.add_message(message=m)

        return messages
