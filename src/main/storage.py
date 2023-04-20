"""Will handle access and storage of messages"""
import os
import logging


logger = logging.getLogger("__name__")


class Storage:
    """Handles storage"""

    def __init__(self) -> None:
        pass


class Mesages(Storage):
    """Handles storage of Messages"""

    def __init__(self) -> None:
        Storage.__init__(self)

        self.home_directory = os.path.expanduser("~")
        self.messages_filepath = os.path.join(self.home_directory, "messages")

    def store_messages(self) -> None:
        """Will store more than 1 message"""
        logger.info("Storing messages")

    def store_message(self) -> None:
        """Will store 1 message"""
        logger.info("Storing 1 message")

    def open_history(self) -> None:
        """Will access"""
        logger.info("Opening history of the following chat")
