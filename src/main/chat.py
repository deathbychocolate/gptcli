"""
Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import logging
import readline

from src.main.openai_helper import OpenAIHelper

logger = logging.getLogger(__name__)


class Chat:
    """
    A chat session
    """

    def __init__(self, model):
        self.model = model

        self._configure_chat()

    def start(self) -> None:
        """
        Will start the chat session that allows USER to AI communication (like texting)
        """
        logger.info("Starting chat")
        while True:
            # check for KeyboardInterrupt and EOFError
            try:
                user_input = input(">>> USER: ")
            except KeyboardInterrupt as exception:
                logger.info("Keyboard interrupt detected")
                logger.exception(exception)
                break
            except EOFError as exception:
                logger.info("EOF detected")
                logger.exception(exception)
                break

            # check for chat session commands
            user_input_length = len(user_input)
            if user_input_length == 0:
                continue
            elif user_input == "exit":
                break

            response = OpenAIHelper(self.model, user_input).send()
            print(">>> AI:", response)

    def _configure_chat(self) -> None:
        logger.info("Configuring chat")
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")
