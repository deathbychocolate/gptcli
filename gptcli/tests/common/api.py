"""Holds the tests for api_helper.py"""

import time
from typing import Generator

import pytest
from pytest import CaptureFixture

from gptcli.src.common.api import (
    Chat,
    SingleExchange,
    Spinner,
    SpinnerProgress,
    SpinnerRecognizing,
    SpinnerThinking,
)
from gptcli.src.common.constants import ProviderNames
from gptcli.src.common.message import Message, MessageFactory, Messages


class TestSpinner:

    @pytest.fixture(scope="function")
    def setup_teardown(self) -> Generator[Spinner, None, None]:
        spinner: Spinner = Spinner(label="Custom Message")
        yield spinner

    def test_spinner_starts_printing_frames(self, setup_teardown: Spinner, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        spinner: Spinner = setup_teardown

        # When run the Spinner for 0.05 seconds.
        with spinner:
            time.sleep(0.05)

        # Then the output to stdout should contain the spinner label.
        out, err = capfd.readouterr()
        assert "Custom Message" in out

    def test_spinner_does_not_show_checkmark_on_completion(
        self, setup_teardown: Spinner, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a Spinner.
        spinner: Spinner = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with spinner:
            time.sleep(0.05)

        # Then the output should not contain a checkmark.
        out, err = capfd.readouterr()
        assert "✔" not in out

    def test_spinner_stops_printing_frames(self, setup_teardown: Spinner, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        spinner: Spinner = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with spinner:
            time.sleep(0.05)
        capfd.readouterr()  # drain output

        # When we wait for the printing to stop.
        time.sleep(0.05)
        out, err = capfd.readouterr()

        # Then no new spinner output should have appeared after exit.
        assert out == ""

    def test_spinner_is_reusable(self, setup_teardown: Spinner, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        spinner: Spinner = setup_teardown

        # When we run the Spinner twice in succession.
        with spinner:
            time.sleep(0.05)
        capfd.readouterr()  # drain first run

        with spinner:
            time.sleep(0.05)

        # Then the second run should also produce output.
        out, err = capfd.readouterr()
        assert "Custom Message" in out


class TestSpinnerProgress:

    @pytest.fixture(scope="function")
    def setup_teardown(self) -> Generator[SpinnerProgress, None, None]:
        spinner: SpinnerProgress = SpinnerProgress(total=3, interval=0.01)
        yield spinner

    def test_spinner_starts_printing_frames(self, setup_teardown: SpinnerProgress, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a SpinnerProgress.
        spinner: SpinnerProgress = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with spinner:
            time.sleep(0.05)

        # Then the output to stdout should contain the progress label.
        out, err = capfd.readouterr()
        assert "Processing" in out

    def test_spinner_shows_checkmark_on_completion(
        self, setup_teardown: SpinnerProgress, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a SpinnerProgress.
        spinner: SpinnerProgress = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with spinner:
            time.sleep(0.05)

        # Then the output should contain a green checkmark and the label.
        out, err = capfd.readouterr()
        assert "✔" in out
        assert "Processing" in out

    def test_spinner_shows_error_indicator_on_failure(
        self, setup_teardown: SpinnerProgress, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a SpinnerProgress.
        spinner: SpinnerProgress = setup_teardown

        # When we raise inside the with block.
        with pytest.raises(RuntimeError):
            with spinner:
                time.sleep(0.05)
                raise RuntimeError("failure")

        # Then the output should contain the error indicator and the label.
        out, err = capfd.readouterr()
        assert "✗" in out
        assert "Processing" in out

    def test_spinner_resets_after_failure(self, setup_teardown: SpinnerProgress, capfd: CaptureFixture[str]) -> None:

        # Given a SpinnerProgress that previously failed.
        spinner: SpinnerProgress = setup_teardown
        with pytest.raises(RuntimeError):
            with spinner:
                time.sleep(0.05)
                raise RuntimeError("failure")
        capfd.readouterr()  # drain first run

        # When we run the spinner again successfully.
        with spinner:
            time.sleep(0.05)

        # Then the output should contain a checkmark, not an error indicator.
        out, err = capfd.readouterr()
        assert "✔" in out
        assert "✗" not in out


class TestSpinnerRecognizing:

    @pytest.fixture(scope="function")
    def setup_teardown(self) -> Generator[SpinnerRecognizing, None, None]:
        recognizing_spinner: SpinnerRecognizing = SpinnerRecognizing(interval=0.01)
        yield recognizing_spinner

    def test_spinner_starts_printing_frames(
        self, setup_teardown: SpinnerRecognizing, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a Spinner.
        recognizing_spinner: SpinnerRecognizing = setup_teardown

        # When run the Spinner for 0.05 seconds.
        with recognizing_spinner:
            time.sleep(0.05)

        # Then the output to stdout should contain the word 'Recognizing'.
        out, err = capfd.readouterr()
        assert "Recognizing" in out

    def test_spinner_shows_checkmark_on_completion(
        self, setup_teardown: SpinnerRecognizing, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a SpinnerRecognizing.
        recognizing_spinner: SpinnerRecognizing = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with recognizing_spinner:
            time.sleep(0.05)

        # Then the output should contain a green checkmark and the label.
        out, err = capfd.readouterr()
        assert "✔" in out
        assert "Recognizing" in out

    def test_spinner_shows_error_indicator_on_failure(
        self, setup_teardown: SpinnerRecognizing, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a SpinnerRecognizing.
        recognizing_spinner: SpinnerRecognizing = setup_teardown

        # When we raise inside the with block.
        with pytest.raises(RuntimeError):
            with recognizing_spinner:
                time.sleep(0.05)
                raise RuntimeError("failure")

        # Then the output should contain the error indicator and the label.
        out, err = capfd.readouterr()
        assert "✗" in out
        assert "Recognizing" in out

    def test_spinner_stops_printing_frames(
        self, setup_teardown: SpinnerRecognizing, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a Spinner.
        recognizing_spinner: SpinnerRecognizing = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with recognizing_spinner:
            time.sleep(0.05)
        capfd.readouterr()  # drain output

        # When we wait for the printing to stop.
        time.sleep(0.05)
        out, err = capfd.readouterr()

        # Then no new spinner output should have appeared after exit.
        assert out == ""


class TestSpinnerThinking:

    @pytest.fixture(scope="function")
    def setup_teardown(self) -> Generator[SpinnerThinking, None, None]:
        thinking_spinner: SpinnerThinking = SpinnerThinking(interval=0.01)
        yield thinking_spinner

    def test_spinner_starts_printing_frames(self, setup_teardown: SpinnerThinking, capfd: CaptureFixture[str]) -> None:

        # Given we have instantiated a Spinner.
        thinking_spinner: SpinnerThinking = setup_teardown

        # When run the Spinner for 0.05 seconds.
        with thinking_spinner:
            time.sleep(0.05)

        # Then the output to stdout should contain the word 'Thinking'.
        out, err = capfd.readouterr()
        assert "Thinking" in out

    def test_spinner_does_not_show_checkmark_on_completion(
        self, setup_teardown: SpinnerThinking, capfd: CaptureFixture[str]
    ) -> None:

        # Given we have instantiated a SpinnerThinking.
        thinking_spinner: SpinnerThinking = setup_teardown

        # When we run the Spinner for 0.05 seconds.
        with thinking_spinner:
            time.sleep(0.05)

        # Then the output should not contain a checkmark.
        out, err = capfd.readouterr()
        assert "✔" not in out

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

            def test_should_return_none_on_failure(self, setup_teardown: Chat) -> None:
                helper: Chat = setup_teardown
                response: Message | None = helper.send()
                assert response is None
