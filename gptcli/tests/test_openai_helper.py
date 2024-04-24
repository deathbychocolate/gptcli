"""File to hold tests related to AskOpenAI"""

import pytest

from gptcli.src.api_helper import OpenAIHelper
from gptcli.src.message import Message, MessageFactory


class TestMessage:
    @pytest.fixture(scope="session")
    def setup(self):
        message = Message("user", "Hello")
        return message.to_dictionary()

    def test_should_return_a_type_to_dictionary(self, setup):
        dictionary = setup
        assert type(dictionary) is dict

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
        message = factory.create_message("user", "Hello")
        assert type(message) is Message


class TestOpenAIHelper:
    @pytest.fixture(scope="session")
    def setup(self):
        helper = OpenAIHelper(OpenAIHelper.GPT_DEFAULT, "Good morning!")
        return helper
