"""File to hold tests related to AskOpenAI"""

import pytest

from gptcli.src.api_helper import OpenAIHelper
from gptcli.src.message import Message, MessageFactory


class TestMessage:
    """Holds all the tests for the Message object"""

    @pytest.fixture(scope="session")
    def setup(self):
        message = Message(role="user", content="Hello", model=OpenAIHelper.GPT_3_5, is_reply=False)
        return message.to_dictionary_reduced_context()

    def test_should_return_a_type_to_dictionary(self, setup):
        dictionary = setup
        assert isinstance(dictionary, dict)

    def test_should_return_a_dictionary_with_a_role_key(self, setup):
        dictionary = setup
        assert dictionary.get("role") is not None

    def test_should_return_a_dictionary_with_a_content_key(self, setup):
        dictionary = setup
        assert dictionary.get("content") is not None


class TestMessageFactory:
    @pytest.fixture(scope="session")
    def setup(self):
        factory = MessageFactory()
        return factory

    def test_should_create_a_message(self, setup):
        factory = setup
        message = factory.create_user_message(role="user", content="Hello", model=OpenAIHelper.GPT_3_5)
        assert isinstance(message, Message)

class TestOpenAIHelper:
    @pytest.fixture(scope="session")
    def setup(self):
        helper = OpenAIHelper(OpenAIHelper.GPT_DEFAULT, "Good morning!")
        return helper
