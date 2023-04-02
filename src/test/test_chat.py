"""
Holds tests for chat sessions
"""

import pytest

from src.main.openai_helper import OpenAIHelper
from src.main.chat import Chat


class TestHandleChatCommands:
    @pytest.fixture(scope="session")
    def setup_teardown(self):
        gpt_3_5 = OpenAIHelper.GPT_ALL[0]
        chat_session = Chat(model=gpt_3_5)

        yield chat_session

    def test_should_accept_an_exit_string_and_perform_a_system_exit(self, setup_teardown):
        chat_session = setup_teardown
        with pytest.raises(SystemExit):
            chat_session._handle_chat_commands(user_input="exit")
        assert True

    def test_should_accept_an_empty_string_and_not_perform_a_system_exit(self, setup_teardown):
        chat_session = setup_teardown
        chat_session._handle_chat_commands(user_input="")
        assert True
