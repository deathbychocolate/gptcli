"""File that will hold all the tests relating to chat.py."""

from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from prompt_toolkit.auto_suggest import Suggestion
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.history import History, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from gptcli.src.common.constants import (
    MistralModelsChat,
    MistralUserRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    ProviderNames,
    UserRoles,
)
from gptcli.src.modes.chat import (
    Chat,
    ChatInstall,
    ChatUser,
    CommandAutoSuggest,
    CommandCompleter,
    _longest_common_prefix,
)


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

        @staticmethod
        def _handler_for(kb: KeyBindings, *keys: str) -> Any:
            return kb.get_bindings_for_keys(keys)[0].handler

        def test_up_arrow_moves_history_backward(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer
            self._handler_for(kb, "up")(fake_event)
            fake_buffer.history_backward.assert_called_once()
            fake_buffer.history_forward.assert_not_called()

        def test_down_arrow_moves_history_forward(self, setup_teardown: Chat) -> None:
            kb: KeyBindings = setup_teardown._configure_key_bindings()
            fake_buffer = MagicMock()
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer
            self._handler_for(kb, "down")(fake_event)
            fake_buffer.history_forward.assert_called_once()
            fake_buffer.history_backward.assert_not_called()


class TestChatInstall:
    """Holds tests for the ChatInstall class.

    ChatInstall only inherits from Chat with no additional methods.
    Add tests here as new functionality is introduced.
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[ChatInstall, None, None]:
        """Generate a ChatInstall object."""
        yield ChatInstall(provider=ProviderNames.OPENAI.value)

    def test_session_uses_in_memory_history(self, setup_teardown: ChatInstall) -> None:
        assert isinstance(setup_teardown.session.history, InMemoryHistory)


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


class TestLongestCommonPrefix:
    """Tests for the _longest_common_prefix function."""

    def test_returns_empty_string_for_empty_list(self) -> None:
        assert _longest_common_prefix([]) == ""

    def test_returns_single_element_unchanged(self) -> None:
        assert _longest_common_prefix(["/help"]) == "/help"

    def test_returns_common_prefix(self) -> None:
        assert _longest_common_prefix(["/dev-clear", "/dev-show"]) == "/dev-"

    def test_returns_empty_string_when_no_common_prefix(self) -> None:
        assert _longest_common_prefix(["abc", "xyz"]) == ""

    def test_returns_full_string_when_all_identical(self) -> None:
        assert _longest_common_prefix(["/help", "/help", "/help"]) == "/help"


class TestCommandAutoSuggest:
    """Tests for the CommandAutoSuggest class."""

    @pytest.fixture()
    def commands(self) -> dict[str, str]:
        return {"/help": "Show help", "/quit": "Quit", "/dev-clear": "Clear"}

    @pytest.fixture()
    def suggest(self, commands: dict[str, str]) -> CommandAutoSuggest:
        return CommandAutoSuggest(commands)

    @staticmethod
    def _suggest(suggest: CommandAutoSuggest, text: str) -> Suggestion | None:
        return suggest.get_suggestion(MagicMock(), Document(text, len(text)))

    class TestGetSuggestion:
        """Tests for CommandAutoSuggest.get_suggestion()."""

        def test_returns_none_for_non_slash_input(self, suggest: CommandAutoSuggest) -> None:
            assert TestCommandAutoSuggest._suggest(suggest, "hello") is None

        def test_returns_none_for_empty_input(self, suggest: CommandAutoSuggest) -> None:
            assert TestCommandAutoSuggest._suggest(suggest, "") is None

        def test_returns_suffix_of_matching_command(self, suggest: CommandAutoSuggest) -> None:
            result = TestCommandAutoSuggest._suggest(suggest, "/hel")
            assert result is not None
            assert result.text == "p"

        def test_returns_none_when_input_exactly_matches_command(self, suggest: CommandAutoSuggest) -> None:
            assert TestCommandAutoSuggest._suggest(suggest, "/help") is None

        def test_returns_none_when_no_command_matches(self, suggest: CommandAutoSuggest) -> None:
            assert TestCommandAutoSuggest._suggest(suggest, "/zzz") is None


class TestChatUser:
    """Tests for the ChatUser class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[ChatUser, None, None]:
        """Generate a ChatUser object."""
        yield ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)

    class TestConfigDoc:
        """Holds tests for ChatUser._config_doc()."""

        def test_contains_required_fields(self, setup_teardown: ChatUser) -> None:
            config: str = setup_teardown._config_doc()
            for field in (
                "Provider",
                "Model",
                "Role (user)",
                "Role (model)",
                "Role (system)",
                "Context",
                "Stream",
                "Store",
                "Encryption",
            ):
                assert field in config

        def test_reflects_constructor_values(self) -> None:
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

    class TestReplaceBufferText:
        """Tests for ChatUser._replace_buffer_text()."""

        def test_deletes_current_text_and_inserts_new(self) -> None:
            fake_buffer = MagicMock()
            ChatUser._replace_buffer_text(fake_buffer, "/hel", "/help")
            fake_buffer.delete_before_cursor.assert_called_once_with(4)
            fake_buffer.insert_text.assert_called_once_with("/help")

        def test_empty_current_text_only_inserts(self) -> None:
            fake_buffer = MagicMock()
            ChatUser._replace_buffer_text(fake_buffer, "", "/help")
            fake_buffer.delete_before_cursor.assert_called_once_with(0)
            fake_buffer.insert_text.assert_called_once_with("/help")

    class TestTabCycling:
        """Tests for the Tab key handler registered by _add_tab_cycling().

        Each test creates a fresh ChatUser so the cycle closure state is clean.
        OpenAI commands starting with '/dev-': /dev-clear, /dev-show (in that order).
        Their LCP is '/dev-', and '/d' → LCP '/dev' across all three /dev* commands.
        """

        @staticmethod
        def _fresh_chat() -> ChatUser:
            return ChatUser(model=OpenaiModelsChat.default(), provider=ProviderNames.OPENAI.value)

        @staticmethod
        def _tab_handler(chat: ChatUser) -> Any:
            return chat._kb.get_bindings_for_keys(("c-i",))[0].handler

        @staticmethod
        def _make_event(text: str) -> MagicMock:
            fake_buffer = MagicMock()
            fake_buffer.document.text_before_cursor = text
            fake_event = MagicMock()
            fake_event.app.current_buffer = fake_buffer
            return fake_event

        def test_does_nothing_for_non_slash_input(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            event = self._make_event("hello")
            handler(event)
            event.app.current_buffer.insert_text.assert_not_called()
            event.app.current_buffer.delete_before_cursor.assert_not_called()

        def test_does_nothing_when_no_matches(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            event = self._make_event("/zzz")
            handler(event)
            event.app.current_buffer.insert_text.assert_not_called()

        def test_single_match_inserts_remaining_suffix(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            event = self._make_event("/hel")
            handler(event)
            event.app.current_buffer.insert_text.assert_called_once_with("p")

        def test_multiple_matches_expands_to_lcp(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            # "/d" matches /developer, /dev-clear, /dev-show — LCP is "/dev"
            event = self._make_event("/d")
            handler(event)
            buf = event.app.current_buffer
            buf.delete_before_cursor.assert_called_once_with(len("/d"))
            buf.insert_text.assert_called_once_with("/dev")

        def test_tab_at_lcp_begins_cycling_with_first_match(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            # "/dev-" is already the LCP of [/dev-clear, /dev-show]
            event = self._make_event("/dev-")
            handler(event)
            buf = event.app.current_buffer
            buf.delete_before_cursor.assert_called_once_with(len("/dev-"))
            buf.insert_text.assert_called_once_with("/dev-clear")

        def test_continuing_cycle_advances_to_next_match(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            handler(self._make_event("/dev-"))  # arm cycle: index=0 → /dev-clear
            second_event = self._make_event("/dev-clear")
            handler(second_event)  # continue cycle: index=1 → /dev-show
            buf = second_event.app.current_buffer
            buf.delete_before_cursor.assert_called_once_with(len("/dev-clear"))
            buf.insert_text.assert_called_once_with("/dev-show")

        def test_cycle_wraps_around_to_first_match(self) -> None:
            chat = self._fresh_chat()
            handler = self._tab_handler(chat)
            handler(self._make_event("/dev-"))  # index=0 → /dev-clear
            handler(self._make_event("/dev-clear"))  # index=1 → /dev-show
            wrap_event = self._make_event("/dev-show")
            handler(wrap_event)  # index wraps → /dev-clear
            buf = wrap_event.app.current_buffer
            buf.delete_before_cursor.assert_called_once_with(len("/dev-show"))
            buf.insert_text.assert_called_once_with("/dev-clear")
