"""
File to hold tests related to AskOpenAI
"""

import pytest

from src.main.api_helper import Message
from src.main.api_helper import MessageFactory
from src.main.api_helper import OpenAIHelper


class TestMessage:
    @pytest.fixture(scope="session")
    def setup(self):
        message = Message("user", "Hello")
        return message.dictionary

    def test_should_return_a_type_dictionary(self, setup):
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
        helper = OpenAIHelper(OpenAIHelper.DEFAULT_ENGINE, "Good morning!")
        return helper

    def test_should_return_a_type_string(self, setup):
        helper = setup
        reply = helper.send()
        assert type(reply) is str

    def test_should_create_chat_completion(self, setup):
        helper = setup
        chat_completion = helper._create_chat_completion()
        assert type(chat_completion) is dict

    def test_should_retrieve_chat_completion_content(self, setup):
        helper = setup
        content = helper._retrieve_chat_completion_content()
        assert type(content) is str

    def test_should_build_messages(self, setup):
        assert False
        # _build_messages(, question: str) -> list:
