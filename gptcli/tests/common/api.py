"""Holds the tests for api_helper.py"""

import time
from typing import Generator

import pytest
import requests
from pytest import CaptureFixture

from gptcli.src.common.api import (
    Chat,
    SingleExchange,
    SpinnerThinking,
)
from gptcli.src.common.constants import ProviderNames
from gptcli.src.common.message import Message, MessageFactory, Messages


class TestSpinnerThinking:

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[SpinnerThinking, None, None]:
        thinking_spinner: SpinnerThinking = SpinnerThinking(interval=0.01)
        yield thinking_spinner

    def test_spinner_starts_printing_frames(self, setup_teardown: SpinnerThinking, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        thinking_spinner: SpinnerThinking = setup_teardown

        # When run the Spinner for 0.05 seconds.
        with thinking_spinner:
            time.sleep(0.05)

        # Then the output to stdout should be 'Thinking ' followed by a line bar.
        out, err = capfd.readouterr()
        assert out.startswith("\rThinking ")

    def test_spinner_stops_printing_frames(self, setup_teardown: SpinnerThinking, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        thinking_spinner: SpinnerThinking = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with thinking_spinner:
            time.sleep(0.05)
        capfd.readouterr()  # drain output

        # When we wait for the printing to stop.
        time.sleep(0.05)
        out, err = capfd.readouterr()

        # Then no new spinner output should have appeared after exit.
        assert out == ""


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
