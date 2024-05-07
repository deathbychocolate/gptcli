"""Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import json
import logging
import readline
from typing import Dict, List

import sseclient
from requests import Response
from requests.exceptions import ChunkedEncodingError

from gptcli.src.api_helper import OpenAIHelper
from gptcli.src.decorators import user_triggered_abort
from gptcli.src.ingest import PDF, Text
from gptcli.src.message import Message, MessageFactory, Messages

logger = logging.getLogger(__name__)


class Chat:
    """A simple chat session"""

    def __init__(self):
        self._configure_chat()

    def _configure_chat(self) -> None:
        logger.info("Configuring chat")
        self._clear_history()
        self._add_arrow_key_support()

    def _clear_history(self) -> None:
        logger.info("Clearing chat history")
        readline.clear_history()

    def _add_arrow_key_support(self) -> None:
        logger.info("Adding arrow key support")
        readline.parse_and_bind(r"'\e[A': history-search-backward")
        readline.parse_and_bind(r"'\e[B': history-search-forward")
        readline.parse_and_bind(r"'\e[C': forward-char")
        readline.parse_and_bind(r"'\e[D': backward-char")

    @user_triggered_abort
    def prompt(self, prompt_text: str) -> str:
        """Prompt user with specified text"""
        user_input = str(input(prompt_text))

        return user_input

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

    def __init__(
        self,
        model,
        role_user: str = "user",
        role_model: str = "assistant",
        context: str = "off",
        stream: str = "on",
        filepath: str = "",
    ):
        Chat.__init__(self)

        self._model = model
        self._role_user = role_user
        self._role_model = role_model
        self._context = True if context == "on" else False
        self._stream = True if stream == "on" else False
        self._filepath = filepath
        self._messages = Messages()

    @user_triggered_abort
    def start(self) -> None:
        """Start a chat session. Expect to see the following output to terminal:

        >>> [MESSAGE]: hi
        >>> [REPLY, model=gpt-4]: Hello! How can I help you today?
        >>> [MESSAGE]:
        """
        logger.info("Starting chat")

        # check if we should add file content to message
        if self._filepath is not None and len(self._filepath) > 0:

            self._print_gptcli_message(f"Loading '{self._filepath}' content as context.")

            message: Message = None
            if Text.is_text(filepath=self._filepath):
                message = MessageFactory.create_user_message(
                    role=self._role_user,
                    content=Text(filepath=self._filepath).extract_text(),
                    model=self._model,
                )
            elif PDF.is_pdf(filepath=self._filepath):
                message = MessageFactory.create_user_message(
                    role=self._role_user,
                    content=PDF(filepath=self._filepath).extract_text(),
                    model=self._model,
                )
            else:
                message = MessageFactory.create_user_message(role=self._role_user, content="", model=self._user)

            self._messages.add_message(message)

        # in chat commands
        exit_commands = set(["exit", "q"])

        # commence chat loop
        while True:
            user_input = self.prompt(">>> [MESSAGE]: ")
            if len(user_input) == 0:
                continue
            elif user_input in exit_commands:
                self._print_gptcli_message("Bye!")
                break
            else:
                user_input = self._check_for_multiline_input(user_input)
                self._add_user_input_to_messages(user_input)
                response = self._send_messages()
                self._add_reply_to_messages(response)
                self._messages = Messages() if self._context is False else self._messages

    def _check_for_multiline_input(self, user_input: str) -> str:

        if user_input == '"""':
            user_input_multiline: List[str] = list()
            user_input_single_line = str(input("... "))

            while user_input_single_line != '"""':
                user_input_multiline.append(user_input_single_line)
                user_input_single_line = str(input("... "))

            user_input = "\n".join(user_input_multiline)

        else:
            return user_input

        return user_input

    def _add_user_input_to_messages(self, user_input) -> None:
        message = MessageFactory.create_user_message(role=self._role_user, content=user_input, model=self._model)
        self._messages.add_message(message)

    def _send_messages(self) -> Response:
        payload: List[Dict] = [message.to_dictionary_reduced_context() for message in self._messages.messages]
        response = OpenAIHelper(self._model, payload=payload, stream=self._stream).send()
        return response

    def _add_reply_to_messages(self, response) -> None:
        message = self._reply(response, stream=self._stream)
        self._messages.add_message(message)

    def _reply(self, response: Response, stream: bool) -> Message:
        logger.info("Selecting reply mode")
        message: Message = None
        if response is None:
            self._print_none()
        else:
            if stream:
                message = self._print_stream(response)
            else:
                message = self._print_simple(response)

        return message

    def _print_none(self) -> None:
        logger.info("Reply mode -> None")
        self._print_gptcli_message("POST request was not completed successfully. Turn on logging to see why.")

    def _print_stream(self, response: Response) -> Message:
        logger.info("Reply mode -> Stream")
        payload = ""
        try:
            self._print_reply("", end="")
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data != "[DONE]":
                    delta = json.loads(event.data)["choices"][0]["delta"]
                    if delta.get("content") is not None:
                        text = delta["content"]
                        print(text, end="", flush=True)
                        payload = "".join([payload, text])
            print("")
        except ChunkedEncodingError:
            print("")
            self._print_gptcli_message("ChunkedEncodingError detected. Maybe try again.")

        message = MessageFactory.create_reply_message(role=self._role_model, content=payload, model=self._model)

        return message

    def _print_simple(self, response: Response) -> Message:
        logger.info("Reply mode -> Simple")
        content = json.loads(response.content)["choices"][0]["message"]["content"]
        self._print_reply(content)

        message = MessageFactory.create_reply_message(role=self._role_model, content=content, model=self._model)

        return message

    def _print_reply(self, text: str, end="\n") -> None:
        logger.info("Printing reply")
        reply = "".join([f">>> [REPLY, model={self._model}]: ", text])
        print(reply, end=end)
