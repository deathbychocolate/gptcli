"""File that will hold all the tests relating to test_constants.py."""

import pytest
import requests
from requests import Response

from gptcli.src.common.constants import MistralModelsChat


class TestMistralModelsChat:

    @pytest.mark.parametrize("model", [class_var.value for class_var in MistralModelsChat])
    def test_should_successfully_send_a_message_to_the_api(self, model: str) -> None:
        url: str = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer Sn5WvVZGDA0jKykp3v59kUeche4KjAjQ",
        }
        body = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": "Only show the number, which is bigger? 1 or 2?"}],
        }
        response: Response = requests.post(url=url, headers=headers, stream=False, json=body, timeout=30)
        assert response.status_code == 200

    class TestDefault:

        def test_should_return_str_type(self) -> None:
            assert isinstance(MistralModelsChat.default(), str)
