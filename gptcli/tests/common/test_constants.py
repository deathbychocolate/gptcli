"""File that will hold all the tests relating to test_constants.py."""

import os

import pytest
import requests
from requests import Response

from gptcli.constants import (
    MISTRAL_API_KEY,
    MISTRAL_ENDPOINT_CHAT_COMPLETIONS,
    OPENAI_API_KEY,
    OPENAI_ENDPOINT_CHAT_COMPLETIONS,
)
from gptcli.src.common.constants import MistralModelsChat, OpenaiModelsChat


class TestMistralModelsChat:

    @pytest.mark.parametrize("model", [class_var.value for class_var in MistralModelsChat])
    def test_should_successfully_send_a_message_to_the_api_given_a_valid_model(self, model: str) -> None:
        url: str = MISTRAL_ENDPOINT_CHAT_COMPLETIONS
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + os.environ[MISTRAL_API_KEY],
        }
        body = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": "Only show the number, which is bigger? 1 or 2?"}],
        }
        response: Response = requests.post(url=url, headers=headers, stream=False, json=body, timeout=30)
        assert response.status_code == 200, f"API request failed: {response.status_code} - {response.text}"

    class TestDefault:

        def test_should_return_str_type(self) -> None:
            assert isinstance(MistralModelsChat.default(), str)


class TestOpenaiModelsChat:

    @pytest.mark.parametrize("model", [class_var.value for class_var in OpenaiModelsChat])
    def test_should_successfully_send_a_message_to_the_api_given_a_valid_model(self, model: str) -> None:
        url: str = OPENAI_ENDPOINT_CHAT_COMPLETIONS
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + os.environ[OPENAI_API_KEY],
        }
        body = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": "Only show the number, which is bigger? 1 or 2?"}],
        }
        response: Response = requests.post(url=url, headers=headers, stream=False, json=body, timeout=30)
        assert response.status_code == 200, f"API request failed: {response.status_code} - {response.text}"

    class TestDefault:

        def test_should_return_str_type(self) -> None:
            assert isinstance(OpenaiModelsChat.default(), str)
