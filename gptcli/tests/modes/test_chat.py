"""File that will hold all the tests relating to chat.py."""

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.history import History, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings

from gptcli.src.common.constants import OpenaiModelsChat, ProviderNames
from gptcli.src.modes.chat import Chat, ChatInstall, ChatUser


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
            history: History | None | InMemoryHistory = chat.session.history
            if isinstance(history, type(None)):
                assert False

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
            history: History | None | InMemoryHistory = chat.session.history
            if isinstance(history, type(None)):
                assert False

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
            history: InMemoryHistory = setup_teardown.session.history

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
