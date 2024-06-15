"""Holds al lthe code related to Single-Exchange communication/transactions."""

import json
from typing import Union

from requests import Response

from gptcli.src.openai_api_helper import OpenAiHelper
from gptcli.src.message import Message, MessageFactory, Messages


class SingleExchange:
    """A Single-Exchange session gices the user the option to use GPTCLI for 1 message and 1 reply and exit."""

    def __init__(
        self,
        input_string: str,
        model: str,
        role_user: str = "user",
        role_model: str = "assistant",
        filepath: str = "",
        storage: bool = True,
    ) -> None:
        self._input_string: str = input_string
        self._model: str = model
        self._role_user: str = role_user
        self._role_model: str = role_model
        self._filepath: str = filepath
        self._storage: bool = storage

    def start(self) -> None:
        """Start Single-Exchange communication."""
        message: Message = MessageFactory.create_user_message(
            role=self._role_user,
            content=self._input_string,
            model=self._model,
        )
        messages: Messages = Messages(messages=[message])
        helper: OpenAiHelper = OpenAiHelper(model=self._model, messages=messages)
        response: Union[Response | None] = helper.send()
        if response:
            message_content: str = json.loads(response.content.decode())["choices"][0]["message"]["content"]
            print(message_content)
