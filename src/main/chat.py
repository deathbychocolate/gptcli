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
        self._clear_history()
        self._add_arrow_key_support()

    def _clear_history(self) -> None:
        logger.info("Clearing chat history")
        readline.clear_history()

    def _add_arrow_key_support(self) -> None:
        logger.info("Adding arrow key support")
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")


class ChatInstall(Chat):
    """A chat session for when we are installing GPTCLI"""

    def __init__(self):
        Chat.__init__(self)

class ChatOpenai(Chat):
    """A chat session for communicating with Openai"""

    def __init__(self, model, stream="on"):
        Chat.__init__(self)

        self.model = model
        self.stream = True if stream == "on" else False

    def start(self) -> None:
        """Will start the chat session that allows USER to AI communication (like texting)"""
        logger.info("Starting chat")
        while True:
            user_input = self.prompt(">>> [MESSAGE]: ")

            if len(user_input) != 0:
                # handle chat commands
                if user_input == "exit":
                    break
                elif user_input.startswith("!"):
                    logger.info("Chat command detected")
                    chat_command = user_input.split("!", maxsplit=1)[1]
                    if chat_command == "set context on":
                        print(">>> [GPTCLI]: CONTEXT ON")
                        continue  # TODO: FEATURE: for when we add context parameter
                    elif chat_command == "set context off":
                        print(">>> [GPTCLI]: CONTEXT OFF")
                        continue  # TODO: FEATURE: for when we add context parameter
                    elif chat_command.startswith("set model "):
                        print(">>> [GPTCLI]: MODEL model")
                        continue  # TODO: FEATURE: add dynamic model switching
                    else:
                        print(">>> [GPTCLI]: UNKNOWN COMMAND DETECTED")
                else:
                    response = OpenAIHelper(self.model, user_input, stream=self.stream).send()
                    self._reply(response, stream=self.stream)

    def _reply(self, response: Response, stream: bool) -> None:
        logger.info("Selecting reply mode")
        if response is None:
            self._reply_none()
        else:
            if stream:
                self._reply_stream(response)
            else:
                self._reply_simple(response)

    def _reply_none(self) -> None:
        logger.info("Reply mode -> None")
        print(">>> [GPTCLI]: Unable to send message(s) due to an exception, maybe try again later.")

    def _reply_stream(self, response: Response) -> None:
        logger.info("Reply mode -> Stream")
        try:
            print(f">>> [REPLY, model={self.model}]: ", end="")
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data != "[DONE]":
                    delta = json.loads(event.data)["choices"][0]["delta"]
                    if delta.get("content") is not None:
                        text = delta["content"]
                        print(text, end="", flush=True)
            print("")
        except EOFError:
            print("\n>>> [GPTCLI]: EOFError detected")
        except KeyboardInterrupt:
            print("\n>>> [GPTCLI]: KeyboardInterrupt detected")

    def _reply_simple(self, response: Response) -> None:
        logger.info("Reply mode -> Simple")
        text = json.loads(response.content)["choices"][0]["message"]["content"]
        print(f">>> [REPLY, model={self.model}]: {text}")
