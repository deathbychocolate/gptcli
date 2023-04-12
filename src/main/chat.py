"""
Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import json
import sys
import logging
import readline

from requests import Response
import sseclient

from src.main.openai_helper import OpenAIHelper

logger = logging.getLogger(__name__)


class Chat:
    """A chat session"""

    def __init__(self, model, stream="on"):
        self.model = model
        self.stream = True if stream == "on" else False

        self._configure_chat()

    def start(self) -> None:
        """Will start the chat session that allows USER to AI communication (like texting)"""
        logger.info("Starting chat")
        while True:
            user_input = self._prompt_user()

            if len(user_input) != 0:
                self._handle_chat_commands(user_input)
                response = OpenAIHelper(self.model, user_input, stream=self.stream).send()
                self._reply(response, stream=self.stream)

    def _prompt_user(self) -> str:
        try:
            user_input = input(">>> [USER]: ")
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
        elif user_input == "context on":
            pass  # TODO for when we add context parameter
        elif user_input == "context off":
            pass  # TODO for when we add context parameter

    def _reply(self, response: Response, stream: bool) -> None:
        if response is None:
            print(">>> [GPTCLI]: ", end="")
            self._reply_none()
        else:
            print(f">>> [AI, model={self.model}]: ", end="")
            if stream:
                self._reply_stream(response)
            else:
                self._reply_simple(response)

    def _reply_none(self) -> None:
        print("Unable to send message(s) due to an exception, maybe try again later.")

    def _reply_stream(self, response: Response) -> None:
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data != "[DONE]":
                delta = json.loads(event.data)["choices"][0]["delta"]
                if delta.get("content") is not None:
                    text = delta["content"]
                    print(text, end="", flush=True)
        print("")

    def _reply_simple(self, response: Response) -> None:
        text = json.loads(response.content)["choices"][0]["message"]["content"]
        print(text)

    def _configure_chat(self) -> None:
        logger.info("Configuring chat")
        self._add_arrow_key_support()

    def _add_arrow_key_support(self) -> None:
        logger.info("Adding arrow key support")
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")
