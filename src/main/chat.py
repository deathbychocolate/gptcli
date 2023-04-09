"""
Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import sys
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
            user_input = self._prompt_user()

            if len(user_input) != 0:
                self._handle_chat_commands(user_input)
                response = OpenAIHelper(self.model, user_input).send()]
                # TODO: maybe add markdown support. See here: https://python.plainenglish.io/dump-the-plain-text-help-in-your-command-line-interfaces-today-3282225274dd
                print(">>> AI:", response)

    def _prompt_user(self) -> str:
        try:
            user_input = input(">>> USER: ")
        except KeyboardInterrupt as exception:
            logger.info("Keyboard interrupt detected")
            logger.exception(exception)
            sys.exit()
        except EOFError as exception:
            logger.info("EOF detected")
            logger.exception(exception)
            sys.exit()

        return user_input

    def _handle_chat_commands(self, user_input: str) -> None:
        if user_input == "exit":
            sys.exit()

    def _configure_chat(self) -> None:
        logger.info("Configuring chat")
        self._add_arrow_key_support()

    def _add_arrow_key_support(self) -> None:
        logger.info("Adding arrow key support")
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")
