"""
Holds tests for chat sessions
"""

import pytest

from src.main.api_helper import OpenAIHelper
from src.main.chat import Chat


class TestHandleChatCommands:
    @pytest.fixture(scope="session")
    def setup(self):
        gpt_3_5 = OpenAIHelper.GPT_ALL[0]
        chat_session = Chat(model=gpt_3_5)
        return chat_session

    def test_should_accept_an_exit_string_and_perform_a_system_exit(self, setup):
        chat_session = setup
        with pytest.raises(SystemExit):
            chat_session._handle_chat_commands(user_input="exit")

    def test_should_accept_an_empty_string_and_not_perform_a_system_exit(self, setup):
        chat_session = setup
        chat_session._handle_chat_commands(user_input="")
        assert True


class TestPromptUser:
    @pytest.fixture(scope="session")
    def setup(self):
        gpt_3_5 = OpenAIHelper.GPT_ALL[0]
        chat_session = Chat(model=gpt_3_5)
        return chat_session

    def test_should_accept_keyboard_interrupt_and_perform_a_system_exit(self, setup, monkeypatch):
        chat_session = setup
        # TODO monkeypatch does not work this way, fix it
        monkeypatch.setattr('builtins.input', lambda _: KeyboardInterrupt)
        with pytest.raises(SystemExit):
            chat_session._prompt_user()

    def test_should_accept_eof_error_and_perform_a_system_exit(self, setup, monkeypatch):
        chat_session = setup
        # TODO monkeypatch does not work this way, fix it
        monkeypatch.setattr('builtins.input', lambda _: EOFError)
        with pytest.raises(SystemExit):
            chat_session._prompt_user()

    def test_should_accept_string_input_and_return_the_same_string_input(self, setup, monkeypatch):
        chat_session = setup
        monkeypatch.setattr('builtins.input', lambda _: "this is test input")
        text = chat_session._prompt_user()
        assert text == "this is test input"
