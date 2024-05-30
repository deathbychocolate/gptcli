"""Contains a wrapper for the openai SDK"""

import json
import logging
import os
from http import HTTPStatus
from logging import Logger
from typing import Union

import requests
from requests import Response
from requests.exceptions import ReadTimeout

from gptcli.src.message import Messages

logger: Logger = logging.getLogger(__name__)


class OpenAiHelper:
    """A helper for OpenAI's API

    It includes information and tools specifically for interacting with OpenAI's API.
    """

    GPT_3_5_MAX_TOKENS = 4_096
    GPT_4_MAX_TOKENS = 8_192
    GPT_4_32K_MAX_TOKENS = 32_768

    def __init__(self, model: str, messages: Messages, stream=False):
        self._model: str = model
        self._messages: list[dict] = [message.to_dictionary_reduced_context() for message in messages]
        self._stream: bool = stream

    def send(self) -> Union[Response | None]:
        """Sends message(s) to openai

        :return: The response string from openai
        """
        logger.info("Sending message to openai")
        self._export_api_key_to_environment_variable()
        key: str = os.environ["OPENAI_API_KEY"]
        response: Union[Response | None] = self._post_request(key=key)

        return response

    def is_valid_api_key(self, key: str) -> bool:
        """Sends a POST request to the Openai API.
        We expect a return of True if we have a valid key and false if not.
        """
        response: Union[Response | None] = self._post_request(key=key)
        if response is None:
            return False
        else:
            is_valid = True if response.status_code == 200 else False

        return is_valid

    def _export_api_key_to_environment_variable(self) -> None:
        if "OPENAI_API_KEY" not in os.environ:
            logger.info("Exporting API key to environment variable")

            # get api key from file
            bash_script_path = os.path.join(os.path.expanduser("~"), ".gptcli/keys/openai")
            with open(bash_script_path, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.read()
        else:
            logger.info("API key already in environment variable")

    def _post_request(self, key: str) -> Response | None:
        logger.info("POSTing request to openai API")

        request_url = "https://api.openai.com/v1/chat/completions"
        request_headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        request_body = {
            "model": self._model,
            "stream": self._stream,
            "messages": self._messages,
        }

        response: Union[Response | None] = None  # return None rather than uninitiated variable
        try:
            response = requests.post(
                request_url,
                headers=request_headers,
                stream=self._stream,
                json=request_body,
                timeout=30,
            )
        # Python errors reference: https://platform.openai.com/docs/guides/error-codes/python-library-error-types
        except ReadTimeout:
            logger.exception("The server did not send any data in the allotted amount of time")
        except TimeoutError:
            logger.exception("This is likely an issue with the API")
        except requests.exceptions.ConnectionError:
            logger.exception("This is likely a local issue")
        except KeyboardInterrupt:
            logger.exception("This is likely manual user intervention")  # when the user decides to exit during a POST

        # Http error codes reference: https://platform.openai.com/docs/guides/error-codes/api-errors
        if response is not None:  # response retrieved
            code: int = response.status_code
            if code >= 400:
                match code:
                    case HTTPStatus.UNAUTHORIZED.value:  # 401
                        logger.warning("Received UNAUTHORIZED client error")
                    case HTTPStatus.NOT_FOUND.value:  # 404
                        logger.warning("Received NOT_FOUND client error")
                    case HTTPStatus.TOO_MANY_REQUESTS.value:  # 429
                        logger.warning("Received TOO_MANY_REQUESTS client error")
                    case HTTPStatus.SERVICE_UNAVAILABLE.value:  # 503
                        logger.warning("Received SERVICE_UNAVAILABLE server error")
                    case _ if code >= 400 and code < 500:
                        logger.warning("Received unexpected client error")
                    case _ if code >= 500 and code < 600:
                        logger.warning("Received unexpected server error")
                    case _ if code >= 600:
                        logger.warning("Response code not recongnized!")
                error = json.loads(response.content)["error"]
                log_message = ":".join(
                    [
                        error["message"],
                        error["type"],
                        error["code"],
                    ]
                )
                logger.warning(log_message)
                response = None
        else:
            logger.warning("Response not retrieved. Replying with None")
            response = None

        return response
