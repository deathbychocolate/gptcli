"""Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import json
import logging
import os
import readline
from logging import Logger
from typing import Set, Union

import sseclient
from requests import Response
from requests.exceptions import ChunkedEncodingError

from gptcli.src.decorators import allow_graceful_chat_exit, user_triggered_abort
from gptcli.src.ingest import PDF, Text
from gptcli.src.message import Message, MessageFactory, Messages
from gptcli.src.openai_api_helper import OpenAiHelper
from gptcli.src.storage import Storage

logger: Logger = logging.getLogger(__name__)


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
        user_input: str = str(input(prompt_text))

        return user_input

    def _print_gptcli_message(self, text: str) -> None:
        logger.info("Printing gptcli message")
        message: str = "".join([">>> [GPTCLI]: ", text])
        print(message)


class ChatInstall(Chat):
    """A chat session for when we are installing GPTCLI"""

    def __init__(self):
        Chat.__init__(self)


class ChatOpenai(Chat):
    """A chat session for communicating with Openai."""

    def __init__(
        self,
        model: str,
        role_user: str = "user",
        role_model: str = "assistant",
        context: bool = True,
        stream: bool = True,
        filepath: str = "",
        storage: bool = True,
        load_last: bool = False
    ):
        Chat.__init__(self)

        self._model: str = model
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._context: bool = context
        self._stream: bool = stream
        self._filepath: str = filepath
        self._storage: bool = storage
        self._load_last: bool = load_last
        self._messages: Messages = Storage().extract_messages() if self._load_last else Messages()

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
            self._extract_file_content_to_message()

        # in chat commands and features
        exit_commands: set = set(["exit", "q"])
        clear_screen_commands: set = set(["clear", "cls"])
        multiline_input: Set[str] = set(['"""'])

        # commence chat loop
        while True:
            user_input = self.prompt(">>> [MESSAGE]: ")
            if user_input in multiline_input:
                user_input = self._scan_multiline_input()
                if len(user_input) == 0 or user_input.isspace():
                    continue
                else:
                    self._process_user_and_reply_messages(user_input)
                    continue
            elif len(user_input) == 0 or user_input.isspace():
                continue
            elif user_input in exit_commands:
                self._print_gptcli_message("Bye!")
                break
            elif user_input in clear_screen_commands:
                os.system("cls" if os.name.casefold() == "nt" else "clear")
                continue
            else:
                self._process_user_and_reply_messages(user_input)
                continue

        # to be executed when exiting the chat loop
        if self._storage is True:
            Storage().store_messages(self._messages, storage_type="chat")

    def _extract_file_content_to_message(self) -> None:
        logger.info("Extracting file content from '%s' to add to message.", self._filepath)

        self._print_gptcli_message(f"Loading '{self._filepath}' content as context.")

        # check if file exists and is supported
        content: str = ""
        if Text.is_text(filepath=self._filepath):
            content = Text(filepath=self._filepath).extract_text()
        elif PDF.is_pdf(filepath=self._filepath):
            content = PDF(filepath=self._filepath).extract_text()
        else:
            self._print_gptcli_message("File not supported or does not exist.")
            self._print_gptcli_message(f"Make sure the filepath you provided is correct: '{self._filepath}'")

        # add content to message for context if content is populated with text
        if len(content) > 0 and not content.isspace():
            message: Message = MessageFactory.create_user_message(
                role=self._role_user,
                content=content,
                model=self._model,
            )
            self._messages.add_message(message)

    def _process_user_and_reply_messages(self, user_input: str) -> None:
        self._add_user_input_to_messages(user_input)
        response: Response = self._send_messages()
        self._add_reply_to_messages(response)
        self._messages = Messages() if self._context is False else self._messages

    def _scan_multiline_input(self) -> str:

        multiline_input: Set = set(['"""'])

        user_input_multiline: list[str] = list()
        user_input_single_line = str(input("... "))

        while user_input_single_line not in multiline_input:
            user_input_multiline.append(user_input_single_line)
            user_input_single_line = str(input("... "))

        user_input = "\n".join(user_input_multiline)

        return user_input

    def _add_user_input_to_messages(self, user_input) -> None:
        message: Message = MessageFactory.create_user_message(
            role=self._role_user,
            content=user_input,
            model=self._model,
        )
        self._messages.add_message(message)

    def _send_messages(self) -> Response:
        response: Response = OpenAiHelper(
            self._model,
            messages=self._messages,
            stream=self._stream,
        ).send()
        return response

    def _add_reply_to_messages(self, response) -> None:
        message: Union[Message | None] = self._reply(response, stream=self._stream)
        self._messages.add_message(message)

    @allow_graceful_chat_exit
    def _reply(self, response: Response, stream: bool) -> Union[Message | None]:
        logger.info("Selecting reply mode")
        message: Union[Message | None] = None
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
        payload: str = ""
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

        message: Message = MessageFactory.create_reply_message(
            role=self._role_model,
            content=payload,
            model=self._model,
        )

        return message

    def _print_simple(self, response: Response) -> Message:
        logger.info("Reply mode -> Simple")
        content: str = json.loads(response.content)["choices"][0]["message"]["content"]
        self._print_reply(content)

        message: Message = MessageFactory.create_reply_message(
            role=self._role_model,
            content=content,
            model=self._model,
        )

        return message

    def _print_reply(self, text: str, end="\n") -> None:
        logger.info("Printing reply")
        reply: str = "".join([f">>> [REPLY, model={self._model}]: ", text])
        print(reply, end=end)
