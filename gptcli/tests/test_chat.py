"""File that will hold all the tests relating to chat.py."""

import readline
from typing import Any, Generator
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

from gptcli.src.chat import Chat


class TestChat:
    """Holds tests for the Chat class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Chat, None, None]:
        c: Chat = Chat()
        yield c

    def test_should_configure_chat(self, setup_teardown: Chat) -> None:
        with patch.object(target=Chat, attribute="_configure_chat") as mock__configure_chat:
            chat: Chat = setup_teardown
            chat.__init__()  # type: ignore # pylint:disable=C2801:unnecessary-dunder-call
            mock__configure_chat.assert_called()

    class TestConfigureChat:
        """Holds tests for the _configure_chat() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_clear_history") as mock__clear_history:
                chat: Chat = setup_teardown
                chat._configure_chat()  # pylint:disable=W0212:protected-access
                mock__clear_history.assert_called()

        def test_should_add_arrow_key_support(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_add_arrow_key_support") as mock__add_arrow_key_support:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock__add_arrow_key_support.assert_called()

    class TestClearHistory:
        """Holds tests for the _clear_history() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="clear_history") as mock_clear_history:
                chat: Chat = setup_teardown
                chat._clear_history()  # pylint:disable=W0212:protected-access
                mock_clear_history.assert_called()

    class TestAddArrowKeySupport:
        """Holds tests for the _add_arrow_key_support() method."""

        def test_should_add_history_search_backward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[A": history-search-backward')

        def test_should_add_history_search_forward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[B": history-search-forward')

        def test_should_add_forward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[C": forward-char')

        def test_should_add_backward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[D": backward-char')

        def test_should_fail_due_to_not_adding_support(self, setup_teardown: Chat) -> None:
            with pytest.raises(expected_exception=AssertionError):
                with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                    chat: Chat = setup_teardown
                    chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                    mock_parse_and_bind.assert_any_call(r"not a real call")

    class TestPrintGptcliMessage:
        """Holds tests for the _print_gptcli_message() method."""

        def test_should_print_boilerplate_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            chat._print_gptcli_message(text="")  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("[GPTCLI]: ")

        def test_should_print_boilerplate_with_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            text: str = "This is a test."
            chat._print_gptcli_message(text=text)  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("".join(["[GPTCLI]: ", text]))


class TestChatInstall:
    """Holds tests for the ChatInstall class.

    The tests are identical to TestChat.
    This is desirable as ChatInstall only inherits from Chat,
    and has no additional methods (for now).

    Feel free to add functionality to it as you please,
    but new functionality should be covered.
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Chat, None, None]:
        c: Chat = Chat()
        yield c

    def test_should_configure_chat(self, setup_teardown: Chat) -> None:
        with patch.object(target=Chat, attribute="_configure_chat") as mock__configure_chat:
            chat: Chat = setup_teardown
            chat.__init__()  # type: ignore # pylint:disable=C2801:unnecessary-dunder-call
            mock__configure_chat.assert_called()

    class TestConfigureChat:
        """Holds tests for the _configure_chat() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_clear_history") as mock__clear_history:
                chat: Chat = setup_teardown
                chat._configure_chat()  # pylint:disable=W0212:protected-access
                mock__clear_history.assert_called()

        def test_should_add_arrow_key_support(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_add_arrow_key_support") as mock__add_arrow_key_support:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock__add_arrow_key_support.assert_called()

    class TestClearHistory:
        """Holds tests for the _clear_history() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="clear_history") as mock_clear_history:
                chat: Chat = setup_teardown
                chat._clear_history()  # pylint:disable=W0212:protected-access
                mock_clear_history.assert_called()

    class TestAddArrowKeySupport:
        """Holds tests for the _add_arrow_key_support() method."""

        def test_should_add_history_search_backward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[A": history-search-backward')

        def test_should_add_history_search_forward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[B": history-search-forward')

        def test_should_add_forward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[C": forward-char')

        def test_should_add_backward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[D": backward-char')

        def test_should_fail_due_to_not_adding_support(self, setup_teardown: Chat) -> None:
            with pytest.raises(expected_exception=AssertionError):
                with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                    chat: Chat = setup_teardown
                    chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                    mock_parse_and_bind.assert_any_call(r"not a real call")

    class TestPrintGptcliMessage:
        """Holds tests for the _print_gptcli_message() method."""

        def test_should_print_boilerplate_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            chat._print_gptcli_message(text="")  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("[GPTCLI]: ")

        def test_should_print_boilerplate_with_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            text: str = "This is a test."
            chat._print_gptcli_message(text=text)  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("".join(["[GPTCLI]: ", text]))


class TestChatOpenai:
    """Holds tests for the ChatOpenai class.

    This class contains all tests from TestChat and more.
    The reason is, we want to confirm that all inherited
    methods work the same as when they were inherited.

    TODO: Add more tests to cover the unique functionality of the ChatOpenai class.
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Chat, None, None]:
        c: Chat = Chat()
        yield c

    def test_should_configure_chat(self, setup_teardown: Chat) -> None:
        with patch.object(target=Chat, attribute="_configure_chat") as mock__configure_chat:
            chat: Chat = setup_teardown
            chat.__init__()  # type: ignore # pylint:disable=C2801:unnecessary-dunder-call
            mock__configure_chat.assert_called()

    class TestConfigureChat:
        """Holds tests for the _configure_chat() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_clear_history") as mock__clear_history:
                chat: Chat = setup_teardown
                chat._configure_chat()  # pylint:disable=W0212:protected-access
                mock__clear_history.assert_called()

        def test_should_add_arrow_key_support(self, setup_teardown: Chat) -> None:
            with patch.object(target=Chat, attribute="_add_arrow_key_support") as mock__add_arrow_key_support:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock__add_arrow_key_support.assert_called()

    class TestClearHistory:
        """Holds tests for the _clear_history() method."""

        def test_should_clear_history(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="clear_history") as mock_clear_history:
                chat: Chat = setup_teardown
                chat._clear_history()  # pylint:disable=W0212:protected-access
                mock_clear_history.assert_called()

    class TestAddArrowKeySupport:
        """Holds tests for the _add_arrow_key_support() method."""

        def test_should_add_history_search_backward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[A": history-search-backward')

        def test_should_add_history_search_forward(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[B": history-search-forward')

        def test_should_add_forward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[C": forward-char')

        def test_should_add_backward_char(self, setup_teardown: Chat) -> None:
            with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                chat: Chat = setup_teardown
                chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                mock_parse_and_bind.assert_any_call(r'"\e[D": backward-char')

        def test_should_fail_due_to_not_adding_support(self, setup_teardown: Chat) -> None:
            with pytest.raises(expected_exception=AssertionError):
                with patch.object(target=readline, attribute="parse_and_bind") as mock_parse_and_bind:
                    chat: Chat = setup_teardown
                    chat._add_arrow_key_support()  # pylint:disable=W0212:protected-access
                    mock_parse_and_bind.assert_any_call(r"not a real call")

    class TestPrintGptcliMessage:
        """Holds tests for the _print_gptcli_message() method."""

        def test_should_print_boilerplate_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            chat._print_gptcli_message(text="")  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("[GPTCLI]: ")

        def test_should_print_boilerplate_with_text(self, capsys: CaptureFixture[str], setup_teardown: Chat) -> None:
            chat: Chat = setup_teardown
            text: str = "This is a test."
            chat._print_gptcli_message(text=text)  # pylint:disable=W0212:protected-access
            captured: Any = capsys.readouterr()
            assert captured.out.startswith("".join(["[GPTCLI]: ", text]))
