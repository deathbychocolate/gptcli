"""Will handle access and storage of messages"""

import json
import logging
import os
from datetime import datetime
from uuid import uuid4

from gptcli.src.message import Message

logger = logging.getLogger("__name__")


class Chat:
    """Specifically handles Chat storage"""

    class Name:
        """Used to generate names for Chats"""

        def generate(self) -> str:
            basename = self._generate_basename()
            file_extension = self._generate_file_extension()
            chat_name = ".".join(
                [
                    basename,
                    file_extension,
                ]
            )

            return chat_name

        def _generate_basename(self) -> str:
            basename = "_".join(
                [
                    "chat",
                    self._generate_date(),
                    self._generate_random_id(),
                ]
            )
            return basename

        def _generate_date(self) -> str:
            date = datetime.now().strftime(r"_%Y_%m_%d__%H_%M_%S_")
            return date

        def _generate_random_id(self) -> str:
            random_id = str(uuid4()).split("-", maxsplit=1)[0]
            return random_id

        def _generate_file_extension(self) -> str:
            return "json"

    class Completion:
        """Chat Completion object used to keep track of storage standard.
        For example, we expect to store messages using the following format:

        {
            "id": "chatcmpl-74cCqMlkbdtCTGGau18UhBy9yKbBB",
            "object": "chat.completion",
            "created": 1681334532,
            "model": "gpt-3.5-turbo-0301",
            "usage": {
                "prompt_tokens": 9,
                "completion_tokens": 9,
                "total_tokens": 18
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How may I assist you today?"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
        """

        def __init__(self) -> None:
            pass

        def generate(self) -> dict:
            return ""

    class Storage:
        def __init__(self) -> None:
            self._home_directory = os.path.expanduser("~")
            self._messages_filepath = os.path.join(self._home_directory, "messages")
            self._name = Chat().Name().generate()
            self._filepath = os.path.join(self._messages_filepath, self._name)

        @property
        def name(self) -> str:
            return self._name

        @property
        def filepath(self) -> str:
            return self._filepath

        def store_messages(self, messages: list[Message]) -> None:
            """Will store multiple message"""
            logger.info("Storing messages")
            for message in messages:
                self._store_message(message)

        def _store_message(self, message: Message) -> None:
            logger.info("Storing message")
            with open(self.filepath, "a", encoding="utf8") as filepointer:
                json.dump(message.dictionary, filepointer, indent=4)
                #  filepointer.write(message.__str__)

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
            with open(self.filepath, "w", encoding="utf8"):
                pass

        def open_history(self) -> None:
            """Will access"""
            logger.info("Opening history of the following chat")
