"""Contains the chat session code

TODO: make better description
It represents the same chat session body that you would see on the chatGPT website
"""

import json
import sys
import logging
import readline

from typing import List, Dict

from requests import Response
from requests.exceptions import ChunkedEncodingError
import sseclient

from src.main.api_helper import OpenAIHelper, Message

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

        self._model = model
        self._stream = True if stream == "on" else False
        self._messages: List[Dict] = [Message("user", "").dictionary()]

    def start(self) -> None:
        """Will start the chat session that allows USER to AI communication (like texting)"""
        logger.info("Starting chat")

        exit_commands = set(["exit", "q"])
        while True:
            user_input = self.prompt(">>> [MESSAGE]: ")

            if len(user_input) != 0:
                # handle chat commands
                if user_input in exit_commands:
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
                    message = Message(role="user", content=user_input).dictionary()
                    self.messages.append(message)
                    response = OpenAIHelper(self._model, payload=self.messages, stream=self.stream).send()
                    message = self._reply(response, stream=self.stream).dictionary()
                    self.messages.append(message)

    def _reply(self, response: Response, stream: bool) -> Message:
        logger.info("Selecting reply mode")

        message: Message = None
        if response is None:
            self._reply_none()
        else:
            if stream:
                # self._reply_fast(response)
                message = self._reply_stream(response)
            else:
                message = self._reply_simple(response)

        return message

    def _reply_none(self) -> None:
        logger.info("Reply mode -> None")
        self._print_gptcli_message("POST request was not completed successfully. Maybe try again.")

    def _reply_stream(self, response: Response) -> Message:
        logger.info("Reply mode -> Stream")
        message = Message("user", "")
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
            message.content = payload
            print("")

        except ChunkedEncodingError:
            print("")  # newline
            self._print_gptcli_message("ChunkedEncodingError detected. Maybe try again.")
        except KeyboardInterrupt:
            print("")  # newline
            self._print_gptcli_message("KeyboardInterrupt detected")

        return message

    def _reply_fast(self, response: Response) -> Message:
        # TODO: FIX: this option is just as slow (if not slower) than the reply_simple method. Try using Rust to do this process.
        # TODO: FEATURE: make this mode available for no chat mode.
        """
        b'data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"role":"assistant"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":"Hello"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":"!"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" How"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" may"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" I"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" assist"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" you"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":" today"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{"content":"?"},"index":0,"finish_reason":null}]}
        data: {"id":"chatcmpl-74cA0XBe8E7kMcyi0B9J8CKSJtXng","object":"chat.completion.chunk","created":1681334356,"model":"gpt-3.5-turbo-0301","choices":[{"delta":{},"index":0,"finish_reason":"stop"}]}
        data: [DONE]
        '
        """
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

    def _reply_simple(self, response: Response) -> Message:
        # TODO: FEATURE: make this mode available for no chat mode.
        logger.info("Reply mode -> Simple")
        text = json.loads(response.content)["choices"][0]["message"]["content"]
        self._print_reply(text)
        message = Message(role="user", content=text)
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
