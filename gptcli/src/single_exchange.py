"""Holds all the code related to Single-Exchange communication/transactions."""

import json
import logging
from logging import Logger
from typing import Union

from requests import Response

from gptcli.src.definitions import extraction_types
from gptcli.src.message import Message, MessageFactory, Messages
from gptcli.src.openai_api_helper import OpenAiHelper

logger: Logger = logging.getLogger(__name__)


class SingleExchange:
    """A Single-Exchange session gives the user the option to use GPTCLI for 1 message and 1 reply and exit."""

    def __init__(
        self,
        input_string: str,
        model: str,
        role_user: str = "user",
        role_model: str = "assistant",
        filepath: str = "",
        storage: bool = True,
        extraction_type: str = "plain",
    ) -> None:
        self._input_string: str = input_string
        self._model: str = model
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._filepath: str = filepath  # TODO: Implement
        self._storage: bool = storage  # TODO: Implement
        self._extraction_type: str = extraction_type

    def start(self) -> None:
        """Start Single-Exchange communication."""
        logger.info("Starting Single-Exchange mode.")
        response = self._build_message_and_generate_response()
        if response:
            text: Union[str | list | dict] = self._choose_extraction_type(
                response=response,
                extraction_type=self._extraction_type,
            )
            print(text)

    def _build_message_and_generate_response(self) -> Response:
        message: Message = MessageFactory.create_user_message(
            role=self._role_user,
            content=self._input_string,
            model=self._model,
        )
        messages: Messages = Messages(messages=[message])
        helper: OpenAiHelper = OpenAiHelper(model=self._model, messages=messages)
        response: Response = helper.send()
        return response

    def _choose_extraction_type(self, response: Response, extraction_type: str) -> Union[str | list | dict]:
        logger.info("Choosing extraction type.")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        if not isinstance(extraction_type, str):
            raise ValueError(f"Parameter 'extraction_type' only accepts str values and not '{type(extraction_type)}'.")
        if extraction_type not in extraction_types.values():
            raise ValueError(f"Parameter 'extraction_type' must be one of '{extraction_types.values()}'.")

        extracted: Union[str | list | dict] = ""
        match extraction_type:
            case "plain":
                extracted = self._extract_message_content(response=response)
            case "choices":
                extracted = self._extract_choices(response=response)
            case "all":
                extracted = self._extract_all(response=response)

        if len(extracted) == 0:
            logger.error("Extracted an empty value when non empty was expected.")
            raise ValueError("Extracted an empty value when non empty was expected.")

        return extracted

    def _extract_message_content(self, response: Response) -> str:
        logger.info("Extracting message content from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        message_content: str = json.loads(response.content.decode())["choices"][0]["message"]["content"]
        return message_content

    def _extract_choices(self, response: Response) -> list:
        logger.info("Extracting choices from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        choices: list = json.loads(response.content.decode())["choices"]
        return choices

    def _extract_all(self, response: Response) -> dict:
        logger.info("Extracting all from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        body: dict = json.loads(response.content.decode())
        return body
