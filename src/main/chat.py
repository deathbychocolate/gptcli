"""Contains the chat session code

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
    """A simple chat session"""

    def __init__(self):
        self._configure_chat()

    def prompt(self, prompt_text: str) -> str:
        """Prompt user with specified text.

        Handles exceptions such as:
        - KeyboardInterrupt
        - EOFError
        """
        try:
            user_input = str(input(prompt_text))
        except KeyboardInterrupt as exception:
            logger.info("Keyboard interrupt detected")
            logger.exception(exception)
            sys.exit()
        except EOFError as exception:
            logger.info("EOF detected")
            logger.exception(exception)
            sys.exit()

        return user_input

    def _configure_chat(self) -> None:
        logger.info("Configuring chat")
        self._add_arrow_key_support()

    def _add_arrow_key_support(self) -> None:
        logger.info("Adding arrow key support")
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")


class ChatInstall(Chat):
    """A chat session for when we are installing GPTCLI"""

    def __init__(self):
        readline.clear_history()


class ChatOpenai(Chat):
    """A chat session for communicating with Openai"""

    def __init__(self, model, stream="on"):
        readline.clear_history()

        self.model = model
        self.stream = True if stream == "on" else False

    def start(self) -> None:
        """Will start the chat session that allows USER to AI communication (like texting)"""
        logger.info("Starting chat")
        while True:
            user_input = self.prompt(">>> [USER]: ")

            if len(user_input) != 0:
                # handle chat commands
                if user_input == "exit":
                    break
                elif user_input == "context on":
                    continue  # TODO for when we add context parameter
                elif user_input == "context off":
                    continue  # TODO for when we add context parameter
                else:
                    response = OpenAIHelper(self.model, user_input, stream=self.stream).send()
                    self._reply(response, stream=self.stream)

    def _reply(self, response: Response, stream: bool) -> None:
        if response is None:
            self._reply_none()
        else:
            if stream:
                self._reply_stream(response)
            else:
                self._reply_simple(response)

    def _reply_none(self) -> None:
        print(">>> [GPTCLI]: Unable to send message(s) due to an exception, maybe try again later.")

    def _reply_stream(self, response: Response) -> None:
        print(f">>> [AI, model={self.model}]: ", end="")
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data != "[DONE]":
                delta = json.loads(event.data)["choices"][0]["delta"]
                if delta.get("content") is not None:
                    text = delta["content"]
                    print(text, end="", flush=True)
        print("")

    def _reply_simple(self, response: Response) -> None:
        print(f">>> [AI, model={self.model}]: ", end="")
        text = json.loads(response.content)["choices"][0]["message"]["content"]
        print(text)
