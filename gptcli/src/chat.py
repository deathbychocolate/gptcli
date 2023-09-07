"""Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import json
import logging
import readline
import sys
from typing import Dict, List

import sseclient
from requests import Response
from requests.exceptions import ChunkedEncodingError

from gptcli.src.api_helper import OpenAIHelper
from gptcli.src.ingest import TextFile
from gptcli.src.message import Message, MessageFactory, Messages

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
        readline.parse_and_bind(r"'\e[A': history-search-backward")
        readline.parse_and_bind(r"'\e[B': history-search-forward")
        readline.parse_and_bind(r"'\e[C': forward-char")
        readline.parse_and_bind(r"'\e[D': backward-char")

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
        self._file_content = (
            Message(self.role_user, TextFile(self.filepath).get_file_content()) if len(filepath) > 0 else None
        )
        self._messages = Messages()

    def start(self) -> None:
        """Start a chat session. Expect to see the following output to terminal:

        >>> [MESSAGE]: hi
        >>> [REPLY, model=gpt-4]: Hello! How can I help you today?
        >>> [MESSAGE]:
        """
        logger.info("Starting chat")

        # check if we should add file content to message
        if self.file_content is not None:
            self._print_gptcli_message(f"Loading '{self.filepath}' content to Messages.")
            self.messages.add_message(self.file_content)

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
                self._add_user_input_to_messages(user_input)
                response = self._send_messages()
                self._add_reply_to_messages(response)
                self.messages = Messages() if self.context is False else self.messages

    def _add_user_input_to_messages(self, user_input) -> None:
        message = MessageFactory.create_message(role=self.role_user, content=user_input)
        self.messages.add_message(message)

    def _send_messages(self) -> Response:
        response = OpenAIHelper(self._model, payload=self.messages.messages, stream=self.stream).send()
        return response

    def _add_reply_to_messages(self, response) -> None:
        message = self._reply(response, stream=self.stream)
        self.messages.add_message(message)

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
        self._print_gptcli_message("POST request was not completed successfully. Maybe try again.")

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
        except KeyboardInterrupt:
            print("")
            self._print_gptcli_message("KeyboardInterrupt detected")

        message = MessageFactory.create_message(role=self.role_model, content=payload)

        return message

    def _print_simple(self, response: Response) -> Message:
        logger.info("Reply mode -> Simple")
        content = json.loads(response.content)["choices"][0]["message"]["content"]
        self._print_reply(content)

        message = MessageFactory.create_message(role=self.role_model, content=content)

        return message

    def _print_reply(self, text: str, end="\n") -> None:
        logger.info("Printing reply")
        reply = "".join([f">>> [REPLY, model={self.model}]: ", text])
        print(reply, end=end)

    @property
    def model(self) -> str:
        return self._model

    @property
    def stream(self) -> bool:
        return self._stream

    @property
    def messages(self) -> List[Dict]:
        return self._messages

    @property
    def context(self) -> str:
        return self._context

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def file_content(self) -> str:
        return self._file_content

    @property
    def role_user(self):
        return self._role_user

    @property
    def role_model(self):
        return self._role_model

    @messages.setter
    def messages(self, value):
        if not isinstance(value, Messages):
            raise ValueError("Was expecting type Messages")
        self._messages = value
