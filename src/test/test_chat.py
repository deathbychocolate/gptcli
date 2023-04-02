"""
Holds tests for chat sessions
"""

import pytest

from src.main.openai_helper import OpenAIHelper
from src.main.chat import Chat


class TestChat:
    @pytest.fixture(scope="session")
    def setup_teardown(self):
        gpt_3_5 = OpenAIHelper.GPT_ALL[0]
        chat_session = Chat(model=gpt_3_5)
        yield chat_session

    def test_should_configure_chat_to_enable_arrow_keys(self, setup_teardown):
        chat_session = setup_teardown()
        chat_session
        assert False

    def test_start_method_should_handle_EOFError_input_by_exiting_loop_gracefully(self, setup_teardown, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda _: EOFError)
        chat_session = setup_teardown
        result = input('Enter your name: ')
        assert result == 'user_input'

    def test_start_method_should_handle_KeyboardInterrupt_input_by_exiting_loop_gracefully(self, setup_teardown):
        assert False

    def test_start_method_should_handle_no_input_by_creating_a_clean_prompt(self, setup_teardown):
        assert False

    def test_start_method_should_handle_EOF_input_by_exiting_loop_gracefully(self, setup_teardown):
        assert False
