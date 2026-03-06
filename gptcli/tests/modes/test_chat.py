"""File that will hold all the tests relating to chat.py."""

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import History, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from gptcli.src.common.constants import (
    MistralModelsChat,
    MistralUserRoles,
    ModelRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    ProviderNames,
    UserRoles,
)
from gptcli.src.modes.chat import Chat, ChatInstall, ChatUser, CommandCompleter


class TestChat:
    """Holds tests for the Chat class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Chat, None, None]:
        """Generate a ChatInstall object."""
        yield Chat()

    class TestInMemoryHistory:
        """Holds tests for confirming we are using InMemoryHistory."""

        def test_session_uses_in_memory_history(self, setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            assert isinstance(chat.session.history, InMemoryHistory)

        def test_history_collects_strings(self, setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            history: History | None = chat.session.history
            assert isinstance(history, InMemoryHistory)

            first_line: str = "first line"
            second_line: str = "second line"
            history.append_string(first_line)
            history.append_string(second_line)

            lines = [line for line in history._storage]

            assert lines == [first_line, second_line]

    class TestKeyBindings:
        """Holds the tests for checking key bindings."""

        def test_should_configure_key_bindings(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_configure_key_bindings") as mock__configure_key_bindings:
                chat: Chat = setup_teardown
                chat.__init__()  # type: ignore # pylint:disable=C2801:unnecessary-dunder-call
                mock__configure_key_bindings.assert_called()

        @staticmethod
        def _handler_for(kb: KeyBindings, *keys: str) -> Any:
            """Returns the handler that is registered for "up" or "down" and down sequences."""
            return kb.get_bindings_for_keys(keys)[0].handler

        def test_key_binding_for_up_arrow_is_registered(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("up",)), "No binding for <up> arrow"

        def test_key_binding_for_down_arrow_is_registered(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("down",)), "No binding for <down> arrow"

        def test_up_arrow_moves_history_backward(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "up")

            # Build a minimal fake event object that contains the bits the
            # handler touches:  event.app.current_buffer.history_backward()
            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_backward.assert_called_once()
            fake_buffer.history_forward.assert_not_called()

        def test_down_arrow_moves_history_forward(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "down")

            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_forward.assert_called_once()
            fake_buffer.history_backward.assert_not_called()


class TestChatInstall:
    """Holds tests for the ChatInstall class.

    The tests are identical to TestChat.
    This is desirable as ChatInstall only inherits from Chat,
    and has no additional methods (for now).

    Feel free to add functionality to it as you please,
    but new functionality should be covered.
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[ChatInstall, None, None]:
        """Generate a ChatInstall object."""
        yield ChatInstall(provider=ProviderNames.OPENAI.value)

    class TestInMemoryHistory:
        """Holds tests that confirm we are using InMemoryHistory."""

        def test_session_uses_in_memory_history(self, setup_teardown: ChatInstall) -> None:
            chat: ChatInstall = setup_teardown
            assert isinstance(chat.session.history, InMemoryHistory)

        def test_history_collects_strings(self, setup_teardown: ChatInstall) -> None:
            chat: ChatInstall = setup_teardown
            history: History | None = chat.session.history
            assert isinstance(history, InMemoryHistory)

            first_line: str = "first line"
            second_line: str = "second line"
            history.append_string(first_line)
            history.append_string(second_line)

            lines = [line for line in history._storage]

            assert lines == [first_line, second_line]

    class TestKeyBindings:
        """Holds the tests for checking key bindings."""

        def test_should_configure_key_bindings(self, setup_teardown: ChatInstall) -> None:
            with patch.object(target=Chat, attribute="_configure_key_bindings") as mock__configure_key_bindings:
                chat: ChatInstall = setup_teardown
                chat.__init__(provider=ProviderNames.OPENAI.value)  # type: ignore[misc]
                mock__configure_key_bindings.assert_called()

        @staticmethod
        def _handler_for(kb: KeyBindings, *keys: str) -> Any:
            """Returns the handler that is registered for "up" or "down" and down sequences."""
            return kb.get_bindings_for_keys(keys)[0].handler

        def test_key_binding_for_up_arrow_is_registered(self, setup_teardown: ChatInstall) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("up",)), "No binding for <up> arrow"

        def test_key_binding_for_down_arrow_is_registered(self, setup_teardown: ChatInstall) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("down",)), "No binding for <down> arrow"

        def test_up_arrow_moves_history_backward(self, setup_teardown: ChatInstall) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "up")

            # Build a minimal fake event object that contains the bits the
            # handler touches:  event.app.current_buffer.history_backward()
            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_backward.assert_called_once()
            fake_buffer.history_forward.assert_not_called()

        def test_down_arrow_moves_history_forward(self, setup_teardown: ChatInstall) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "down")

            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_forward.assert_called_once()
            fake_buffer.history_backward.assert_not_called()


class TestCommandCompleter:
    """Tests for the CommandCompleter class."""

    @pytest.fixture()
    def openai_completer(self) -> CommandCompleter:
        return CommandCompleter(CommandCompleter.commands_for_provider(ProviderNames.OPENAI.value))

    @pytest.fixture()
    def mistral_completer(self) -> CommandCompleter:
        return CommandCompleter(CommandCompleter.commands_for_provider(ProviderNames.MISTRAL.value))

    @staticmethod
    def _complete(completer: CommandCompleter, text: str) -> list[str]:
        """Helper to get completion text values for a given input."""
        doc = Document(text, len(text))
        return [c.text for c in completer.get_completions(doc, CompleteEvent())]

    class TestNoCompletionsForRegularInput:
        """Tests that completions only trigger when input starts with '/'."""

        def test_empty_input(self, openai_completer: CommandCompleter) -> None:
            assert TestCommandCompleter._complete(openai_completer, "") == []

        def test_regular_text(self, openai_completer: CommandCompleter) -> None:
            assert TestCommandCompleter._complete(openai_completer, "hello") == []

        def test_slash_in_middle(self, openai_completer: CommandCompleter) -> None:
            assert TestCommandCompleter._complete(openai_completer, "hello /h") == []

    class TestDynamicFiltering:
        """Tests that completions narrow down as the user types."""

        def test_slash_shows_all_commands(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/")
            assert len(results) > 0

        def test_slash_d_narrows_to_dev_commands(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/d")
            assert all(r.startswith("/d") for r in results)
            assert "/developer" in results
            assert "/dev-clear" in results
            assert "/dev-show" in results

        def test_slash_dev_dash_narrows_further(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/dev-")
            assert "/dev-clear" in results
            assert "/dev-show" in results
            assert "/dev" not in results

        def test_exact_match_returns_nothing(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/help")
            assert results == []

    class TestProviderSpecificCommands:
        """Tests that provider-specific commands are included or excluded."""

        def test_openai_has_dev_commands(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/d")
            assert "/developer" in results

        def test_openai_has_no_sys_commands(self, openai_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(openai_completer, "/s")
            assert not any(r.startswith("/sys") for r in results)

        def test_mistral_has_sys_commands(self, mistral_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(mistral_completer, "/s")
            assert "/system" in results

        def test_mistral_has_no_dev_commands(self, mistral_completer: CommandCompleter) -> None:
            results = TestCommandCompleter._complete(mistral_completer, "/d")
            assert not any(r.startswith("/dev") for r in results)

    class TestCompletionMetadata:
        """Tests that completions include descriptive metadata."""

        def test_completions_have_display_meta(self, openai_completer: CommandCompleter) -> None:
            doc = Document("/h", 2)
            completions = list(openai_completer.get_completions(doc, CompleteEvent()))
            assert len(completions) > 0
            assert all(c.display_meta is not None for c in completions)

    class TestCommandsForProvider:
        """Tests for the commands_for_provider static method."""

        def test_common_commands_present_for_openai(self) -> None:
            commands = CommandCompleter.commands_for_provider(ProviderNames.OPENAI.value)
            assert "/help" in commands
            assert "/quit" in commands
            assert "/mult" in commands

        def test_common_commands_present_for_mistral(self) -> None:
            commands = CommandCompleter.commands_for_provider(ProviderNames.MISTRAL.value)
            assert "/help" in commands
            assert "/quit" in commands
            assert "/mult" in commands

        def test_unknown_provider_has_no_system_commands(self) -> None:
            commands = CommandCompleter.commands_for_provider("unknown")
            assert "/developer" not in commands
            assert "/system" not in commands


class TestChatUser:
    """Holds tests for the ChatUser class.

    The tests are identical to TestChat.
    This is desirable as ChatInstall only inherits from Chat,
    and has no additional methods (for now).

    Feel free to add functionality to it as you please,
    but new functionality should be covered.

    TODO: Add more tests to cover the unique functionality of the ChatOpenai class.
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[ChatUser, None, None]:
        """Generate a ChatUser object."""
        yield ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)

    class TestInMemoryHistory:
        """Holds tests for confirming we are using InMemoryHistory."""

        def test_session_uses_in_memory_history(self, setup_teardown: ChatUser) -> None:
            assert isinstance(setup_teardown.session.history, InMemoryHistory)

        def test_history_collects_strings(self, setup_teardown: ChatUser) -> None:
            history: History | None = setup_teardown.session.history
            assert isinstance(history, InMemoryHistory)

            first_line: str = "first line"
            second_line: str = "second line"
            history.append_string(first_line)
            history.append_string(second_line)

            lines = [line for line in history._storage]

            assert lines == [first_line, second_line]

    class TestKeyBindings:
        """Holds the tests for checking key bindings."""

        def test_should_configure_key_bindings(self, setup_teardown: ChatUser) -> None:
            with patch.object(target=Chat, attribute="_configure_key_bindings") as mock__configure_key_bindings:
                chat: ChatUser = setup_teardown
                chat.__init__(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)  # type: ignore[misc]
                mock__configure_key_bindings.assert_called()

        @staticmethod
        def _handler_for(kb: KeyBindings, *keys: str) -> Any:
            """Returns the handler that is registered for "up" or "down" and down sequences."""
            return kb.get_bindings_for_keys(keys)[0].handler

        def test_key_binding_for_up_arrow_is_registered(self, setup_teardown: ChatUser) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("up",)), "No binding for <up> arrow"

        def test_key_binding_for_down_arrow_is_registered(self, setup_teardown: ChatUser) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            assert kb.get_bindings_for_keys(("down",)), "No binding for <down> arrow"

        def test_up_arrow_moves_history_backward(self, setup_teardown: ChatUser) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "up")

            # Build a minimal fake event object that contains the bits the
            # handler touches:  event.app.current_buffer.history_backward()
            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_backward.assert_called_once()
            fake_buffer.history_forward.assert_not_called()

        def test_down_arrow_moves_history_forward(self, setup_teardown: ChatUser) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            handler = self._handler_for(kb, "down")

            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer

            handler(fake_event)

            fake_buffer.history_forward.assert_called_once()
            fake_buffer.history_backward.assert_not_called()

    class TestConfigDoc:
        """Holds tests for ChatUser._config_doc()."""

        def test_contains_provider(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert ProviderNames.OPENAI.value in config

        def test_contains_model(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert OpenaiModelsChat.default() in config

        def test_contains_role_user(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert UserRoles.default() in config

        def test_contains_role_model(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert ModelRoles.default() in config

        def test_contains_context_setting(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert "Context" in config

        def test_contains_stream_setting(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert "Stream" in config

        def test_contains_store_setting(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert "Store" in config

        def test_contains_encryption_setting(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert "Encryption" in config

        def test_default_values(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            config: str = chat._config_doc()
            assert "True" in config  # context, stream, store are all True by default

        def test_custom_values(self) -> None:
            chat = ChatUser(
                model="gpt-4o",
                provider=ProviderNames.OPENAI.value,
                role_user="developer",
                role_model="assistant",
                context=False,
                stream=False,
                store=False,
            )
            config: str = chat._config_doc()
            assert "gpt-4o" in config
            assert "developer" in config
            assert "False" in config

        def test_contains_role_system(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            assert "Role (system)" in config

    class TestProcessSystemMessage:
        """Tests for ChatUser._process_system_message()."""

        def test_adds_system_message_with_developer_role_for_openai(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("You are a pirate.")
            assert len(chat._messages) == 1
            msg = next(iter(chat._messages))
            assert msg.role == OpenaiUserRoles.system_role()
            assert msg.content == "You are a pirate."

        def test_adds_system_message_with_system_role_for_mistral(self) -> None:
            chat = ChatUser(model=MistralModelsChat.default(), provider=ProviderNames.MISTRAL.value)
            chat._process_system_message("You are a pirate.")
            assert len(chat._messages) == 1
            msg = next(iter(chat._messages))
            assert msg.role == MistralUserRoles.system_role()
            assert msg.content == "You are a pirate."

        def test_ignores_empty_input(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("")
            assert len(chat._messages) == 0

        def test_ignores_whitespace_only_input(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("   \n  ")
            assert len(chat._messages) == 0

        def test_multiple_system_messages_stack(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("You are a pirate.")
            chat._process_system_message("You speak only in rhymes.")
            assert len(chat._messages) == 2

    class TestProcessSystemMessageConfirmation:
        """Tests for the confirmation output after adding a system message."""

        def test_prints_confirmation_after_adding_system_message(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("You are a pirate.")
            captured = capsys.readouterr()
            assert "System message added" in captured.out
            assert "1 active" in captured.out

        def test_confirmation_shows_incrementing_count(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("First.")
            first_captured = capsys.readouterr()
            assert "1 active" in first_captured.out
            chat._process_system_message("Second.")
            second_captured = capsys.readouterr()
            assert "2 active" in second_captured.out

        def test_no_confirmation_for_empty_input(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("")
            captured = capsys.readouterr()
            assert captured.out == ""

    class TestDisplaySystemMessages:
        """Tests for ChatUser._display_system_messages()."""

        def test_displays_no_messages_text(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._display_system_messages()
            captured = capsys.readouterr()
            assert "No active system messages" in captured.out

        def test_displays_system_messages_with_indices(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("You are a pirate.")
            chat._process_system_message("Speak in rhymes.")
            _ = capsys.readouterr()  # discard confirmation output
            chat._display_system_messages()
            captured = capsys.readouterr()
            assert "[1]" in captured.out
            assert "[2]" in captured.out
            assert "pirate" in captured.out
            assert "rhymes" in captured.out

    class TestProcessSystemClear:
        """Tests for ChatUser._process_system_clear()."""

        def test_clears_all_system_messages_without_index(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("First.")
            chat._process_system_message("Second.")
            chat._process_system_clear("/dev-clear")
            assert len(chat._messages) == 0

        def test_clears_single_system_message_by_index(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("First.")
            chat._process_system_message("Second.")
            chat._process_system_clear("/dev-clear 1")
            assert len(chat._messages) == 1
            remaining = next(iter(chat._messages))
            assert remaining.content == "Second."

        def test_prints_error_for_invalid_index(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("First.")
            _ = capsys.readouterr()
            chat._process_system_clear("/dev-clear abc")
            captured = capsys.readouterr()
            assert "Invalid index" in captured.out

        def test_prints_error_for_out_of_range_index(self, capsys: pytest.CaptureFixture[str]) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("First.")
            _ = capsys.readouterr()
            chat._process_system_clear("/dev-clear 99")
            captured = capsys.readouterr()
            assert "No system message at index 99" in captured.out

    class TestProcessSystemClearMistral:
        """Tests for _process_system_clear with Mistral provider."""

        def test_clears_all_system_messages_with_sys_clear(self) -> None:
            chat = ChatUser(model=MistralModelsChat.default(), provider=ProviderNames.MISTRAL.value)
            chat._process_system_message("First.")
            chat._process_system_message("Second.")
            chat._process_system_clear("/sys-clear")
            assert len(chat._messages) == 0

        def test_clears_single_system_message_by_index(self) -> None:
            chat = ChatUser(model=MistralModelsChat.default(), provider=ProviderNames.MISTRAL.value)
            chat._process_system_message("First.")
            chat._process_system_message("Second.")
            chat._process_system_clear("/sys-clear 1")
            assert len(chat._messages) == 1
            remaining = next(iter(chat._messages))
            assert remaining.content == "Second."

    class TestNoContextProtectsSystemMessages:
        """Tests that --no-context preserves system messages."""

        def test_flush_except_preserves_system_messages(self) -> None:
            chat = ChatUser(
                model=OpenaiModelsChat.default(),
                provider=ProviderNames.OPENAI.value,
                context=False,
            )
            chat._process_system_message("You are a pirate.")
            user_msg = chat._message_factory.user_message(
                role=UserRoles.default(),
                content="Hello.",
                model=OpenaiModelsChat.default(),
            )
            chat._messages.add(user_msg)
            # Simulate what _process_user_and_reply_messages does on --no-context
            chat._messages.flush_except({chat._role_system})
            assert len(chat._messages) == 1
            remaining = next(iter(chat._messages))
            assert remaining.role == OpenaiUserRoles.system_role()

    class TestFlushSystemMessages:
        """Tests for system message flush commands."""

        def test_flush_removes_only_system_messages_openai(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            chat._process_system_message("You are a pirate.")
            user_msg = chat._message_factory.user_message(
                role=UserRoles.default(),
                content="Hello.",
                model=OpenaiModelsChat.default(),
            )
            chat._messages.add(user_msg)
            assert len(chat._messages) == 2
            chat._messages.flush_by_role({chat._role_system})
            assert len(chat._messages) == 1
            remaining = next(iter(chat._messages))
            assert remaining.role == "user"

        def test_flush_removes_only_system_messages_mistral(self) -> None:
            chat = ChatUser(model=MistralModelsChat.default(), provider=ProviderNames.MISTRAL.value)
            chat._process_system_message("You are a pirate.")
            user_msg = chat._message_factory.user_message(
                role=UserRoles.default(),
                content="Hello.",
                model=MistralModelsChat.default(),
            )
            chat._messages.add(user_msg)
            assert len(chat._messages) == 2
            chat._messages.flush_by_role({chat._role_system})
            assert len(chat._messages) == 1
            remaining = next(iter(chat._messages))
            assert remaining.role == "user"

    class TestSessionSystem:
        """Tests for ChatUser._session_system."""

        def test_session_system_is_separate_from_session_multiline(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            assert chat._session_system is not chat._session_multiline

        def test_session_system_uses_in_memory_history(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            assert isinstance(chat._session_system.history, InMemoryHistory)

        def test_session_system_is_multiline(self) -> None:
            chat = ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)
            assert chat._session_system.multiline is True
