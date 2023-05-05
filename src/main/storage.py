"""Will handle access and storage of messages"""
import os
import logging

from uuid import uuid4
from datetime import datetime
from src.main.api_helper import Message

logger = logging.getLogger("__name__")


class ChatName:
    """Used to generate names for Chats"""

    def __init__(self) -> None:
        self.name = self._generate_chat_name()

    def _generate_chat_name(self) -> str:
        basename = self._generate_chat_basename()
        file_extension = self._generate_chat_file_extension()
        chat_name = ".".join(
            [
                basename,
                file_extension,
            ]
        )

        return chat_name

    def _generate_chat_basename(self) -> str:
        basename = "_".join(
            [
                "chat",
                self._generate_chat_date(),
                self._generate_chat_random_id(),
            ]
        )
        return basename

    def _generate_chat_date(self) -> str:
        date = datetime.now().strftime(r"_%Y_%m_%d__%H_%M_%S_")
        return date

    def _generate_chat_random_id(self) -> str:
        random_id = str(uuid4()).split("-", maxsplit=1)[0]
        return random_id

    def _generate_chat_file_extension(self) -> str:
        return "json"


class Chat:
    """Specifically handles Chat storage"""

    def __init__(self) -> None:
        self._home_directory = os.path.expanduser("~")
        self._messages_filepath = os.path.join(self._home_directory, "messages")
        self._name = ChatName().name
        self._filepath = os.path.join(self._messages_filepath, self._name)

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def name(self) -> str:
        return self._name

    def store_messages(self, messages: list[Message]) -> None:
        """Will store multiple message"""
        logger.info("Storing messages")
        # TODO add condition for checking if file exists, add comma or not at the end
        for message in messages:
            self._store_message(message)

    def _store_message(self, message: Message) -> None:
        logger.info("Storing message")
        # TODO add condition for checking if file exists
        with open(self._messages_filepath, "a", encoding="utf8") as filepointer:
            filepointer.write(message.__str__)

    def _is_file_present(self) -> bool:
        is_present = False
        try:
            with open(self.filepath, "r", encoding="utf8"):
                pass
        except FileNotFoundError:
            logger.info("Chat not found: %s", self.filepath)
        return is_present

    def _create_file(self) -> None:
        logger.info("Creating file for storage of message(s)")
        with open(self._messages_filepath, "w", encoding="utf8"):
            pass

    def open_history(self) -> None:
        """Will access"""
        logger.info("Opening history of the following chat")
