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

from src.main.api_helper import OpenAIHelper

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

    def _print_gptcli_message(self, text: str) -> None:
        logger.info("Printing gptcli message")
        message = "".join([">>> [GPTCLI]: ", text])
        print(message)


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
                        self._print_gptcli_message("CONTEXT ON")
                        continue  # TODO: FEATURE: for when we add context parameter
                    elif chat_command == "set context off":
                        self._print_gptcli_message("CONTEXT OFF")
                        continue  # TODO: FEATURE: for when we add context parameter
                    elif chat_command.startswith("set model "):
                        self._print_gptcli_message("MODEL model")
                        continue  # TODO: FEATURE: add dynamic model switching
                    else:
                        self._print_gptcli_message("UNKNOWN COMMAND DETECTED")
                else:
                    response = OpenAIHelper(self.model, user_input, stream=self.stream).send()
                    self._reply(response, stream=self.stream)

    def _reply(self, response: Response, stream: bool) -> None:
        logger.info("Selecting reply mode")
        if response is None:
            self._reply_none()
        else:
            if stream:
                # self._reply_fast(response)
                self._reply_stream(response)
            else:
                self._reply_simple(response)

    def _reply_none(self) -> None:
        logger.info("Reply mode -> None")
        self._print_gptcli_message("POST request was not completed successfully. Maybe try again.")

    def _reply_stream(self, response: Response) -> None:
        logger.info("Reply mode -> Stream")
        try:
            self._print_reply("", end="")
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data != "[DONE]":
                    delta = json.loads(event.data)["choices"][0]["delta"]
                    if delta.get("content") is not None:
                        text = delta["content"]
                        print(text, end="", flush=True)
            print("")
        except KeyboardInterrupt:
            print("")  # newline
            self._print_gptcli_message("KeyboardInterrupt detected")

    def _reply_fast(self, response: Response) -> None:
        # TODO: FIX: this option is just as slow (if not slower) than the reply_simple method. Try using Rust to do this process.
        # TODO: FEATURE: make this mode available for no chat mode.
        logger.info("Reply mode -> Fast")

        # clean response content to json ready format
        content = response.content.decode("UTF8")
        content = content.replace("data: ", "")
        content = content.split("\n\n")
        content = content[1:-3]

        # collect all server sent events text into chucks list
        chunks = []
        for data in content:
            chunk = json.loads(data)
            chunk = chunk["choices"][0]["delta"]["content"]
            chunks.append(chunk)

        # concatenate the chunks into a full reply
        reply = "".join(chunks)

        self._print_reply(reply)

    def _reply_simple(self, response: Response) -> None:
        # TODO: FEATURE: make this mode available for no chat mode.
        logger.info("Reply mode -> Simple")
        text = json.loads(response.content)["choices"][0]["message"]["content"]
        self._print_reply(text)

    def _print_reply(self, text: str, end="\n") -> None:
        logger.info("Printing reply")
        reply = "".join([f">>> [REPLY, model={self.model}]: ", text])
        print(reply, end=end)
