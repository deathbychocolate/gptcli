"""Holds the tests for api_helper.py"""

from typing import Generator

import pytest
import requests

from gptcli.src.common.api import (
    Chat,
    SingleExchange,
)
from gptcli.src.common.constants import ProviderNames
from gptcli.src.common.message import Message, MessageFactory, Messages


class TestOpenAiHelper:
    """Holds tests for the class OpenAiHelper."""

    class SingleExchange:

        class TestIsValidApiKey:
            """Holds tests for is_valid_api_key()."""

            def test_should_return_false_for_invalid_api_key(self, setup_teardown: SingleExchange) -> None:
                helper: SingleExchange = setup_teardown
                is_not_valid = not helper.is_valid_api_key(key="invalid_key")
                assert is_not_valid

    class Chat:

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[Chat, None, None]:
            message: Message = MessageFactory(provider=ProviderNames.OPENAI.value).user_message(
                role="user",
                content="Hi!",
                model="gpt-4o",
            )
            messages: Messages = Messages(messages=[message])
            helper = Chat(provider=ProviderNames.OPENAI.value, model="gpt-4o", messages=messages, stream=False)
            yield helper

        class TestSend:
            """Holds tests for send()."""

            def test_should_return_a_message_object(self, setup_teardown: Chat) -> None:
                helper: Chat = setup_teardown
                response: Message = helper.send()
                assert isinstance(response, requests.Response)
