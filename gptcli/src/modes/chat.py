"""Contains the code used to mimic a webapp chat session."""

import logging
import os
import subprocess
from collections.abc import Iterable
from logging import Logger
from textwrap import dedent
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from gptcli.src.common.api import Chat as ChatAPIHelper
from gptcli.src.common.constants import (
    GRN,
    GRY,
    RED,
    RST,
    ChatCommands,
    MistralUserRoles,
    ModelRoles,
    OpenaiUserRoles,
    ProviderNames,
    UserRoles,
)
from gptcli.src.common.decorators import user_triggered_abort
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.ingest import PDF, Text
from gptcli.src.common.message import MessageFactory, Messages
from gptcli.src.common.storage import Storage

logger: Logger = logging.getLogger(__name__)
_PREVIEW_MAX_LENGTH: int = 80


class CommandCompleter(Completer):  # type: ignore[misc]
    """Autocompletes chat commands when input starts with '/'."""

    def __init__(self, commands: dict[str, str]) -> None:
        """Initialize the completer with available commands.

        Args:
            commands (dict[str, str]): Mapping of command strings to their descriptions.
        """
        self._commands: dict[str, str] = commands

    @staticmethod
    def commands_for_provider(provider: str) -> dict[str, str]:
        """Return command-to-description mapping based on the provider.

        Args:
            provider (str): The provider name (e.g. 'openai' or 'mistral').

        Returns:
            dict[str, str]: A mapping of command strings to descriptions.
        """
        commands: dict[str, str] = {
            ChatCommands.MULT.value: "Enter multiline mode",
            ChatCommands.CONFIG.value: "Show current config",
            ChatCommands.CLEAR_UNIX.value: "Clear screen",
            ChatCommands.HELP.value: "Show help",
            ChatCommands.QUIT.value: "End program",
        }

        if provider == ProviderNames.OPENAI.value:
            commands[ChatCommands.DEVELOPER.value] = "Set developer message"
            commands[ChatCommands.DEV_CLEAR.value] = "Clear developer messages"
            commands[ChatCommands.DEV_SHOW.value] = "Show developer messages"
        elif provider == ProviderNames.MISTRAL.value:
            commands[ChatCommands.SYSTEM.value] = "Set system message"
            commands[ChatCommands.SYS_CLEAR.value] = "Clear system messages"
            commands[ChatCommands.SYS_SHOW.value] = "Show system messages"

        return commands

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        """Yield completions for commands matching the current input.

        Args:
            document (Document): The current document/input state.
            complete_event (CompleteEvent): The completion event.

        Yields:
            Completion: Matching command completions.
        """
        text: str = document.text_before_cursor
        if not text.startswith("/"):
            return

        for command, description in self._commands.items():
            if command.startswith(text) and command != text:
                yield Completion(command, start_position=-len(text), display_meta=description)


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
    """A chat session for when the user is chatting with the AI."""

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
        encryption: Encryption | None = None,
        api_key: str = "",
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
            encryption (Encryption | None, optional): Encryption instance for encrypting stored data. Defaults to None.
            api_key (str, optional): The API key for authentication. Defaults to "".
        """
        Chat.__init__(self)
        self.session.completer = CommandCompleter(CommandCompleter.commands_for_provider(provider))

        self._model: str = model
        self._provider: str = provider
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._context: bool = context
        self._stream: bool = stream
        self._filepath: str = filepath
        self._store: bool = store
        self._load_last: bool = load_last
        self._encryption_enabled: bool = encryption is not None
        self._storage: Storage = Storage(provider=provider, encryption=encryption)
        loaded: Messages | None = self._storage.extract_messages() if self._load_last else Messages()
        self._encryption_required: bool = self._load_last and loaded is None
        self._messages: Messages = loaded if loaded is not None else Messages()
        self._message_factory: MessageFactory = MessageFactory(provider=provider)
        self._chat: ChatAPIHelper = ChatAPIHelper(
            provider=provider,
            model=model,
            messages=self._messages,
            stream=stream,
            api_key=api_key,
        )
        self._session_multiline: PromptSession = PromptSession(history=InMemoryHistory(), multiline=True)
        self._session_system: PromptSession = PromptSession(history=InMemoryHistory(), multiline=True)

        match provider:
            case ProviderNames.OPENAI.value:
                self._role_system: str = OpenaiUserRoles.system_role()
                self._commands_system: list[str] = ChatCommands.developer()
                self._commands_system_clear: list[str] = ChatCommands.developer_clear()
                self._commands_system_show: list[str] = ChatCommands.developer_show()
            case ProviderNames.MISTRAL.value:
                self._role_system = MistralUserRoles.system_role()
                self._commands_system = ChatCommands.system()
                self._commands_system_clear = ChatCommands.system_clear()
                self._commands_system_show = ChatCommands.system_show()
            case _:
                raise NotImplementedError(f"No system-message configuration for provider '{provider}'.")

    @user_triggered_abort
    def start(self) -> None:
        """Start a chat session. Expect to see the following output to terminal:

        >>> hi
        Hello! How can I help you today?
        >>>
        """
        logger.info("Starting chat.")

        if self._encryption_required:
            print("Cannot load last session: encryption key required.")
            return None

        # check if we should add file content to message
        count_when_loaded: int = 0
        if self._filepath is not None and len(self._filepath) > 0:
            self._ingest_file_as_context()
        if self._load_last:
            self._storage.display_last_chat()
        if self._load_last:
            count_when_loaded = len(self._messages)

        commands_multiline = ChatCommands.multiline()
        commands_clear = ChatCommands.clear()
        commands_config = ChatCommands.config()
        commands_config_doc = self._config_doc()
        commands_exit = ChatCommands.exit()
        commands_help = ChatCommands.help()
        commands_help_doc = ChatCommands.help_doc(provider=self._provider)
        commands_exec = "cls" if os.name.lower() == "nt" else "clear"

        while True:
            user_input = self.prompt(">>> ")
            if user_input in commands_multiline:
                user_input = self.prompt_multiline("... ")
            elif user_input in self._commands_system:
                system_input = self._prompt_system("... ")
                self._process_system_message(system_input)
                continue
            elif any(user_input == cmd or user_input.startswith(cmd + " ") for cmd in self._commands_system_clear):
                self._process_system_clear(user_input)
                continue
            elif user_input in self._commands_system_show:
                self._display_system_messages()
                continue
            elif user_input.isspace():
                continue
            elif user_input in commands_clear:
                subprocess.run(commands_exec, shell=True, check=True)
                continue
            elif user_input in commands_config:
                print(commands_config_doc)
                continue
            elif user_input in commands_help:
                print(commands_help_doc)
                continue
            elif user_input in commands_exit:
                break

            self._process_user_and_reply_messages(user_input)

        if self._should_store_messages(number_of_messages_from_storage=count_when_loaded):
            self._storage.store_messages(messages=self._messages, model=self._model)

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

    @user_triggered_abort
    def _prompt_system(self, prompt_text: str) -> str:
        """Prompt the user for a system/developer message."""
        return str(
            self._session_system.prompt(
                message=ANSI(f"{GRY}{prompt_text}{RST}"),
                placeholder=ANSI(f"{GRY} Sets model behavior | Esc then Enter to send{RST}"),
                prompt_continuation=ANSI(f"{GRY}{prompt_text}{RST}"),
            )
        )

    def _ingest_file_as_context(self) -> None:
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

    def _process_system_message(self, content: str) -> None:
        """Add a system message to the messages stack without sending to the API.

        Args:
            content (str): The system/developer message content.
        """
        if not content or content.isspace():
            return
        message = self._message_factory.user_message(
            role=self._role_system,
            content=content,
            model=self._model,
        )
        self._messages.add(message)
        count: int = sum(1 for m in self._messages if m.is_system)
        print(f"{GRY}  System message added ({count} active, {message.tokens} tokens).{RST}")

    def _display_system_messages(self) -> None:
        """Display all active system/developer messages with 1-based indices."""
        system_contents: list[str] = [m.content for m in self._messages if m.is_system]
        if not system_contents:
            print(f"{GRY}  No active system messages.{RST}")
            return
        for idx, content in enumerate(system_contents, start=1):
            preview: str = content.replace("\n", " ")
            if len(preview) > _PREVIEW_MAX_LENGTH:
                preview = preview[: _PREVIEW_MAX_LENGTH - 3] + "..."
            print(f"{GRY}  [{idx}] {preview}{RST}")

    def _process_system_clear(self, user_input: str) -> None:
        """Clear all system messages or a single one by index.

        Args:
            user_input (str): The raw command, e.g. "/dev-clear" or "/dev-clear 2".
        """
        parts: list[str] = user_input.strip().split(maxsplit=1)
        if len(parts) == 1:
            self._messages.flush_by_role({self._role_system})
            return
        try:
            index: int = int(parts[1])
        except ValueError:
            print(f"{RED}  Invalid index: '{parts[1]}'. Use a number, e.g. {self._commands_system_clear[0]} 2{RST}")
            return
        removed: bool = self._messages.remove_by_role_and_index(role=self._role_system, index=index - 1)
        if not removed:
            print(f"{RED}  No system message at index {index}.{RST}")

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

        if message_reply is not None:
            self._messages.add(message_reply)

        if not self._context:  # flush if --no-context flag is set
            self._messages.flush_except({self._role_system})

        return None

    def _config_doc(self) -> str:
        """Return a formatted string showing the current chat configuration."""
        return dedent(
            f"""
            Provider:       {self._provider}
            Model:          {self._model}
            Role (user):    {self._role_user}
            Role (model):   {self._role_model}
            Role (system):  {self._role_system}
            Context:        {self._context}
            Stream:         {self._stream}
            Store:          {self._store}
            Encryption:     {self._encryption_enabled}
            """
        )

    def _should_store_messages(self, number_of_messages_from_storage: int) -> bool:
        """Accepts the number of messages loaded from storage and returns true if we added new messages."""
        return self._store and len(self._messages) - number_of_messages_from_storage > 0
