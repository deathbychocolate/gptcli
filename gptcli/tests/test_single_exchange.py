"""File that will hold all the tests relating to Message.py."""

import json
from typing import Generator, Union

import pytest
from requests import Response

from gptcli.src.definitions import extraction_types, openai
from gptcli.src.message import Message, MessageFactory, Messages
from gptcli.src.openai_api_helper import OpenAiHelper
from gptcli.src.single_exchange import SingleExchange


# pylint: disable=W0212:protected-access
class TestSingleExchange:
    """Holds tests for the SingleExchange class."""

    @pytest.fixture(scope="session")
    def single_exchange_fixture(self) -> Generator[SingleExchange, None, None]:
        se: SingleExchange = SingleExchange(
            input_string="Say, hi! Nothing else please.",
            model=openai["GPT_3_5_TURBO"],
            role_user="user",
            role_model="assistant",
            filepath="",
            storage=True,
        )
        yield se

    @pytest.fixture(scope="session")
    def response_fixture(self) -> Generator[Response, None, None]:
        message: Message = MessageFactory.create_user_message(
            role="user",
            content="Hi!",
            model=openai["GPT_4O"],
        )
        messages: Messages = Messages(messages=[message])
        helper: OpenAiHelper = OpenAiHelper(model=openai["GPT_4O"], messages=messages)
        response: Response = helper.send()
        yield response

    class TestBuildMessageAndGenerateResponse:
        """Holds tests for _build_message_and_generate_response()."""

        def test_should_return_response_object(
            self,
            single_exchange_fixture: SingleExchange,
        ):
            se: SingleExchange = single_exchange_fixture
            result: Response = se._build_message_and_generate_response()
            assert isinstance(result, Response)

    class TestChooseExtractionType:
        """Holds tests for _choose_extraction_type()."""

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
            extraction_type,
            expected_type,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            python_object: Union[str | list | dict] = se._choose_extraction_type(
                response=response,
                extraction_type=extraction_types[extraction_type],
            )
            assert isinstance(python_object, expected_type)

        def test_should_raise_value_error_when_parameter_response_is_not_response_object(
            self,
            single_exchange_fixture: SingleExchange,
        ):
            se: SingleExchange = single_exchange_fixture
            response: dict = dict()
            with pytest.raises(ValueError):
                se._choose_extraction_type(
                    response=response,  # type: ignore
                    extraction_type=extraction_types["plain"],
                )

        def test_should_raise_value_error_when_parameter_extraction_type_is_not_string_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            with pytest.raises(ValueError):
                se._choose_extraction_type(
                    response=response,
                    extraction_type=-1,  # type: ignore
                )

        def test_should_raise_value_error_when_parameter_extraction_type_does_not_contain_valid_value(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            with pytest.raises(ValueError):
                se._choose_extraction_type(
                    response=response,
                    extraction_type="not a valid type",  # type: ignore
                )

    class TestExtractMessageContent:
        """Holds tests for _extract_choices()."""

        def test_should_accept_parameter_of_type_response(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_message_content(response=response)

        def test_should_extract_message_content_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: str = json.loads(response.content.decode())["choices"][0]["message"]["content"]
            extracted_message_content: str = se._extract_message_content(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ):
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_message_content(response=None)  # type: ignore

        def test_should_return_string(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
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
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_choices(response=response)

        def test_should_extract_choices_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: str = json.loads(response.content.decode())["choices"]
            extracted_message_content: list = se._extract_choices(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ):
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_choices(response=None)  # type: ignore

        def test_should_return_deserialized_json_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            extracted_message_content: list = se._extract_choices(response=response)
            assert isinstance(extracted_message_content, list)

    class TestExtractAll:
        """Holds tests for _extract_all()."""

        def test_should_accept_parameter_of_type_response(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            se._extract_all(response=response)

        def test_should_extract_choices_from_response_parameter(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            expected_text: str = json.loads(response.content.decode())
            extracted_message_content: dict = se._extract_all(response=response)
            assert expected_text == extracted_message_content

        def test_should_raise_value_error(
            self,
            single_exchange_fixture: SingleExchange,
        ):
            se: SingleExchange = single_exchange_fixture
            with pytest.raises(ValueError):
                se._extract_all(response=None)  # type: ignore

        def test_should_return_deserialized_json_object(
            self,
            single_exchange_fixture: SingleExchange,
            response_fixture: Response,
        ):
            se: SingleExchange = single_exchange_fixture
            response: Response = response_fixture
            extracted_message_content: dict = se._extract_all(response=response)
            assert isinstance(extracted_message_content, dict)
