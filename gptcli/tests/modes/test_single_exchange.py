"""File that will hold all the tests relating to Message.py."""

import json
from typing import Any, Generator

import pytest
from requests import Response

from gptcli.src.common.constants import (
    OpenaiModelRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    OutputTypes,
    ProviderNames,
)
from gptcli.src.modes.single_exchange import SingleExchange


# pylint: disable=W0212:protected-access
class TestSingleExchange:
    """Holds tests for the SingleExchange class."""

    @pytest.fixture(scope="session")
    def single_exchange_fixture(self) -> Generator[SingleExchange, None, None]:
        se: SingleExchange = SingleExchange(
            input_string="Say, hi! Nothing else please.",
            model=OpenaiModelsChat.GPT_3_5_TURBO.value,
            provider=ProviderNames.OPENAI.value,
            role_user=OpenaiUserRoles.USER.value,
            role_model=OpenaiModelRoles.ASSISTANT.value,
            filepath="",
        )
        yield se

    @pytest.fixture(scope="session")
    def response_fixture(self) -> Generator[Response, None, None]:
        """Generate a custom/fake response to avoid making an over the wire API call."""
        fake_response_payload: dict[str, Any] = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "annotations": [],
                        "content": "Hello! How can I assist you today?",
                        "refusal": None,
                        "role": "assistant",
                    },
                }
            ],
            "created": 1752870195,
            "id": "chatcmpl-Bultr8SYJNuW5CBybbUG1xOq57M8u",
            "model": "o4-mini-2025-04-16",
            "object": "chat.completion",
            "service_tier": "default",
            "system_fingerprint": None,
            "usage": {
                "completion_tokens": 91,
                "completion_tokens_details": {
                    "accepted_prediction_tokens": 0,
                    "audio_tokens": 0,
                    "reasoning_tokens": 64,
                    "rejected_prediction_tokens": 0,
                },
                "prompt_tokens": 7,
                "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0},
                "total_tokens": 98,
            },
        }
        response: Response = Response()
        response.status_code = 200
        response._content = json.dumps(fake_response_payload).encode()
        yield response

    class TestChooseExtractionType:
        """Holds tests for _choose_output()."""

        @pytest.mark.parametrize(
            "extraction_type,expected_type",
            [
                ("plain", str),
                ("choices", list),
                ("all", dict),
            ],
        )
        def test_should_return_the_corresponding_type(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
            extraction_type: str,
            expected_type: type,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            python_object: str | list[dict[str, Any]] | dict[str, Any] = se._choose_output(
                response=response,
                output=extraction_type,
            )
            assert isinstance(python_object, expected_type)

        def test_should_raise_value_error_when_parameter_response_is_not_response_object(
            self,
            single_exchange_fixture: SingleExchange,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: dict[str, Any] = dict()
            with pytest.raises(ValueError):
                se._choose_output(
                    response=response,  # type: ignore
                    output=OutputTypes.PLAIN.value,
                )

        def test_should_raise_value_error_when_parameter_extraction_type_is_not_string_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            with pytest.raises(ValueError):
                se._choose_output(
                    response=response,
                    output="",
                )

        def test_should_raise_value_error_when_parameter_extraction_type_does_not_contain_valid_value(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            with pytest.raises(ValueError):
                se._choose_output(
                    response=response,
                    output="not a valid type",
                )

    class TestExtractMessageContent:
        """Holds tests for _extract_choices()."""

        def test_should_accept_parameter_of_type_response(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_message_content(response=response)

        def test_should_extract_message_content_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: str = json.loads(response.content.decode())["choices"][0]["message"]["content"]
            extracted_message_content: str = se._extract_message_content(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_message_content(response=None)  # type: ignore

        def test_should_return_string(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            extracted_message_content: str = se._extract_message_content(response=response)
            assert isinstance(extracted_message_content, str)

    class TestExtractChoices:
        """Holds tests for _extract_choices()."""

        def test_should_accept_parameter_of_type_response(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_choices(response=response)

        def test_should_extract_choices_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: list[dict[str, Any]] = json.loads(response.content.decode())["choices"]
            extracted_message_content: list[dict[str, Any]] = se._extract_choices(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_choices(response=None)  # type: ignore

        def test_should_return_deserialized_json_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            extracted_message_content: list[dict[str, Any]] = se._extract_choices(response=response)
            assert isinstance(extracted_message_content, list)

    class TestExtractAll:
        """Holds tests for _extract_all()."""

        def test_should_accept_parameter_of_type_response(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_all(response=response)

        def test_should_extract_choices_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: dict[str, Any] = json.loads(response.content.decode())
            extracted_message_content: dict[str, Any] = se._extract_all(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_all(response=None)  # type: ignore

        def test_should_return_deserialized_json_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ) -> None:
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            extracted_message_content: dict[str, Any] = se._extract_all(response=response)
            assert isinstance(extracted_message_content, dict)
