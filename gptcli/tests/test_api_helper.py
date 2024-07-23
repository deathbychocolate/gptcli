"""Holds the tests for api_helper.py"""

import pytest
import requests

from gptcli.src.message import Message, MessageFactory, Messages
from gptcli.src.openai_api_helper import OpenAiHelper


class TestOpenAiHelper:
    """Holds tests for the class OpenAiHelper."""

    @pytest.fixture(scope="session")
    def setup_teardown(self):
        message: Message = MessageFactory.create_user_message(role="user", content="Hi!", model="gpt-4-turbo")
        messages: Messages = Messages(messages=[message])
        helper = OpenAiHelper(model="gpt-3.5-turbo", messages=messages, stream=False)
        yield helper

    class TestIsValidApiKey:
        """Holds tests for is_valid_api_key()."""

        def test_should_return_false_for_invalid_api_key(self, setup_teardown: OpenAiHelper) -> None:
            helper: OpenAiHelper = setup_teardown
            is_not_valid = not helper.is_valid_api_key(key="invalid_key")
            assert is_not_valid

    class TestSend:
        """Holds tests for send()."""

        def test_should_return_a_response_object(self, setup_teardown) -> None:
            helper: OpenAiHelper = setup_teardown
            response: requests.Response = helper.send()
            assert isinstance(response, requests.Response)

    class TestExportApiKeyToEnvironmentVariable:
        """Holds tests for _export_api_key_to_environment_variable()."""

        def test_should_return_a_response_object(self, setup_teardown) -> None:
            helper: OpenAiHelper = setup_teardown
            result = helper._export_api_key_to_environment_variable()  # pylint: disable=W0212:protected-access
            assert result is None
