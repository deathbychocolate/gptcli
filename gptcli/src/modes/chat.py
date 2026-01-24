"""Contains the code used to mimic a webapp chat session."""

import logging
import os
from logging import Logger
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from gptcli.src.common.api import Chat as ChatAPIHelper
from gptcli.src.common.constants import (
    GRN,
    GRY,
    RST,
    ChatCommands,
    ModelRoles,
    UserRoles,
)
from gptcli.src.common.decorators import user_triggered_abort
from gptcli.src.common.ingest import PDF, Text
from gptcli.src.common.message import MessageFactory, Messages
from gptcli.src.common.storage import Storage

logger: Logger = logging.getLogger(__name__)


class Chat:
    """A simple chat session."""

    def __init__(self) -> None:
        self.session: PromptSession = PromptSession(
            history=InMemoryHistory(),
            key_bindings=self._configure_key_bindings(),
        )

    @staticmethod
    def _configure_key_bindings() -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")  # type: ignore[misc]
        def _(event: Any) -> None:
            event.app.current_buffer.history_backward()

        @kb.add("down")  # type: ignore[misc]
        def _(event: Any) -> None:
            event.app.current_buffer.history_forward()

        return kb

    @user_triggered_abort
    def prompt(self, prompt_text: str) -> str:
        """Prompt user with prompt text."""
        return str(
            self.session.prompt(
                message=ANSI(f"{GRN}{prompt_text}{RST}"),
                placeholder=ANSI(f"{GRY}Default Placeholder...{RST}"),
            )
        )


class ChatInstall(Chat):
    """A chat session for when we are installing GPTCLI."""

    def __init__(self, provider: str) -> None:
        Chat.__init__(self)

        self._provider: str = provider.capitalize()

    @user_triggered_abort
    def prompt(self, prompt_text: str) -> str:
        """Prompt user with prompt text."""
        return str(
            self.session.prompt(
                message=ANSI(f"{GRN}{prompt_text}{RST}"),
                placeholder=ANSI(f"{GRY}Enter a valid {self._provider} API key...{RST}"),
            )
        )


class ChatUser(Chat):

    def __init__(
        self,
        model: str,
        provider: str,
        role_user: str = UserRoles.default(),
        role_model: str = ModelRoles.default(),
        context: bool = True,
        stream: bool = True,
        filepath: str = "",
        store: bool = True,
        load_last: bool = False,
    ) -> None:
        """A chat session for when the user is chatting with the AI.

        Args:
            model (str): The AI model to use for this chat. See OpenaiModelsChat or MistralModelsChat.
            provider (str): The AI provider to use for this chat, for example 'mistral' or 'openai'.
            role_user (str, optional): The chosen role for the user. Defaults to UserRoles.default().
            role_model (str, optional): The chosen role for the model. Defaults to ModelRoles.default().
            context (bool, optional): Remember previously sent messages. Defaults to True.
            stream (bool, optional): Print the chat replies as a text stream. Defaults to True.
            filepath (str, optional): The filepath of the file to load (text) contents from. Defaults to "".
            store (bool, optional): Store the chat messages to disk. Defaults to True.
            load_last (bool, optional): Load the most recent chat as context. Defaults to False.
        """
        Chat.__init__(self)

        self._model: str = model
        self._provider: str = provider
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._context: bool = context
        self._stream: bool = stream
        self._filepath: str = filepath
        self._store: bool = store
        self._load_last: bool = load_last
        self._storage: Storage = Storage(provider=provider)
        self._messages: Messages = self._storage.extract_messages() if self._load_last else Messages()
        self._message_factory: MessageFactory = MessageFactory(provider=provider)
        self._chat: ChatAPIHelper = ChatAPIHelper(
            provider=provider,
            model=model,
            messages=self._messages,
            stream=stream,
        )
        self._session_multiline: PromptSession = PromptSession(history=InMemoryHistory(), multiline=True)

    @user_triggered_abort
    def start(self) -> None:
        """Start a chat session. Expect to see the following output to terminal:

        >>> hi
        Hello! How can I help you today?
        >>>
        """
        logger.info("Starting chat.")

        # check if we should add file content to message
        count_when_loaded: int = 0
        if self._filepath is not None and len(self._filepath) > 0:
            self._extract_file_content_to_message()
        if self._load_last:
            self._storage.extract_and_show_messages_for_display()
        if self._load_last:
            count_when_loaded = len(self._messages)

        commands_multiline = ChatCommands.multiline()
        commands_clear = ChatCommands.clear()
        commands_exit = ChatCommands.exit()
        commands_help = ChatCommands.help()
        commands_help_doc = ChatCommands.help_doc()
        commands_exec = "cls" if os.name.lower() == "nt" else "clear"

        while True:
            user_input = self.prompt(">>> ")
            if user_input in commands_multiline:
                user_input = self.prompt_multiline("... ")
            elif user_input.isspace():
                continue
            elif user_input in commands_clear:
                os.system(commands_exec)
                continue
            elif user_input in commands_help:
                print(commands_help_doc)
                continue
            elif user_input in commands_exit:
                break

            self._process_user_and_reply_messages(user_input)

        if self._should_store_messages(number_of_messages_from_storage=count_when_loaded):
            self._storage.store_messages(messages=self._messages)

    @user_triggered_abort
    def prompt(self, prompt_text: str) -> str:
        """Prompt the user."""
        return str(
            self.session.prompt(
                message=ANSI(f"{GRN}{prompt_text}{RST}"),
                placeholder=ANSI(f"{GRY}Send a message (/? for help){RST}"),
            )
        )

    @user_triggered_abort
    def prompt_multiline(self, prompt_text: str) -> str:
        """Prompt the user with multiline mode."""

        return str(
            self._session_multiline.prompt(
                message=ANSI(f"{GRN}{prompt_text}{RST}"),
                placeholder=ANSI(f"{GRY} ↑/↓ Navigate history | Esc then Enter to send{RST}"),
                prompt_continuation=ANSI(f"{GRN}{prompt_text}{RST}"),
            )
        )

    def _extract_file_content_to_message(self) -> None:
        logger.info("Extracting file content from '%s' to add to m.", self._filepath)

        print(f"Loading '{self._filepath}' content as context.")

        content: str = ""
        if Text.is_text(filepath=self._filepath):
            content = Text(filepath=self._filepath).extract_text()
        elif PDF.is_pdf(filepath=self._filepath):
            content = PDF(filepath=self._filepath).extract_text()
        else:
            print("File not supported or does not exist.")
            print(f"Make sure the filepath you provided is correct: '{self._filepath}'")

        if len(content) > 0 and not content.isspace():
            message_user = self._message_factory.user_message(role=self._role_user, content=content, model=self._model)
            self._messages.add(message_user)

    def _process_user_and_reply_messages(self, user_input: str) -> None:
        logger.info("Processing user and reply messages.")

        if len(user_input) <= 0 or user_input.isspace():
            return None

        # add user message to chat session
        message_user = self._message_factory.user_message(role=self._role_user, content=user_input, model=self._model)
        self._messages.add(message_user)
        self._chat.messages = self._messages

        # send messages and capture reply
        message_reply = self._chat.send()
        self._messages.add(message_reply)

        if not self._context:  # flush if --no-context flag is set
            self._messages.flush()

        return None

    def _should_store_messages(self, number_of_messages_from_storage: int) -> bool:
        """Accepts the number of messages loaded from storage and returns true if we added new messages."""
        return self._store and len(self._messages) - number_of_messages_from_storage > 0
