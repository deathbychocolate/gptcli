"""Holds all the code related to Single-Exchange communication/transactions."""

import json
import logging
from logging import Logger
from typing import Any

from requests import Response

from gptcli.src.common.api import SingleExchange as SingleExchangeHelper
from gptcli.src.common.constants import (
    MISTRAL,
    OPENAI,
    ModelRoles,
    OutputTypes,
    UserRoles,
)
from gptcli.src.common.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


class SingleExchange:
    """A Single-Exchange session gives the user the option to use GPTCLI for 1 message and 1 reply and exit."""

    def __init__(
        self,
        input_string: str,
        model: str,
        provider: str,
        role_user: str = UserRoles.default(),
        role_model: str = ModelRoles.default(),
        filepath: str = "",
        output: str = OutputTypes.default(),
    ) -> None:
        self._input_string: str = input_string
        self._model: str = model
        self._provider: str = provider
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._filepath: str = filepath  # TODO: Implement
        self._output: str = output

    def start(self) -> None:
        """Start Single-Exchange communication."""
        logger.info("Starting Single-Exchange mode.")
        response = self._build_message_and_generate_response()
        if response:
            text: str | list[dict[str, Any]] | dict[str, Any] = self._choose_output(
                response=response,
                output=self._output,
            )
            print(text)

    def _build_message_and_generate_response(self) -> Response:
        message: Message = MessageFactory(provider=self._provider).user_message(
            role=self._role_user,
            content=self._input_string,
            model=self._model,
        )
        messages: Messages = Messages(messages=[message])
        helper: SingleExchangeHelper | None = None
        if self._provider == MISTRAL:
            helper = SingleExchangeHelper(provider=MISTRAL, model=self._model, messages=messages)
        elif self._provider == OPENAI:
            helper = SingleExchangeHelper(provider=OPENAI, model=self._model, messages=messages)
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")
        response: Response = helper.send()
        return response

    def _choose_output(self, response: Response, output: str) -> str | list[dict[str, Any]] | dict[str, Any]:
        logger.info("Choosing extraction type.")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        if not isinstance(output, str):
            raise ValueError(f"Parameter 'output' only accepts str values and not '{type(output)}'.")
        if output not in OutputTypes.to_list():
            raise ValueError(f"Parameter 'output' must be one of '{OutputTypes.to_list()}'.")

        extracted: str | list[dict[str, Any]] | dict[str, Any] = ""
        match output:
            case OutputTypes.PLAIN.value:
                extracted = self._extract_message_content(response=response)
            case OutputTypes.CHOICES.value:
                extracted = self._extract_choices(response=response)
            case OutputTypes.ALL.value:
                extracted = self._extract_all(response=response)

        if len(extracted) == 0:
            logger.error("Extracted an empty value when non empty was expected.")
            raise ValueError("Extracted an empty value when non empty was expected.")

        return extracted

    @staticmethod
    def _extract_message_content(response: Response) -> str:
        logger.info("Extracting message content from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        message_content: str = json.loads(response.content.decode())["choices"][0]["message"]["content"]
        return message_content

    @staticmethod
    def _extract_choices(response: Response) -> list[dict[str, Any]]:
        logger.info("Extracting choices from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        choices: list[dict[str, Any]] = json.loads(response.content.decode())["choices"]
        return choices

    @staticmethod
    def _extract_all(response: Response) -> dict[str, Any]:
        logger.info("Extracting all from Response object")
        if not isinstance(response, Response):
            raise ValueError(f"Parameter 'response' only accepts Response values and not '{type(response)}'.")
        body: dict[str, Any] = json.loads(response.content.decode())
        return body
