"""Will handle access and storage of messages"""
import os
import logging

from uuid import uuid4
from datetime import datetime
from src.main.api_helper import Message

logger = logging.getLogger("__name__")


class Chats():
    """Handles storage of Messages"""

    def __init__(self) -> None:
        self.home_directory = os.path.expanduser("~")
        self.messages_filepath = os.path.join(self.home_directory, "messages")
        self.chat_name = "_".join(
            [
                "gptcli",
                datetime.now().strftime(r'%Y_%m_%d'),
                str(uuid4()).split("-", maxsplit=1)[0],
                ".json",
            ]
        )
        self.chat_filepath = os.path.join(self.messages_filepath, self.chat_name)

    def store_messages(self, messages: list[Message]) -> None:
        """Will store multiple message"""
        logger.info("Storing messages")
        # TODO add condition for checking if file exists, add comma or not at the end
        for message in messages:
            self._store_message(message)

    def _store_message(self, message: Message) -> None:
        logger.info("Storing message")
        # TODO add condition for checking if file exists
        with open(self.messages_filepath, "a", encoding="utf8") as filepointer:
            filepointer.write(message.__str__)

    def _is_file_present(self) -> bool:
        is_present = False
        try:
            with open(self.chat_filepath, "r", encoding="utf8"):
                pass
        except FileNotFoundError:
            logger.info("Chat not found: %s", self.chat_filepath)
        return is_present

    def _create_file(self) -> None:
        logger.info("Creating file for storage of message(s)")
        with open(self.messages_filepath, "w", encoding="utf8"):
            pass

    def open_history(self) -> None:
        """Will access"""
        logger.info("Opening history of the following chat")
