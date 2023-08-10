"""Contains a wrapper for the openai SDK"""
import logging
import os
from typing import Dict, List

from http import HTTPStatus

import requests
from requests.exceptions import ReadTimeout

logger = logging.getLogger(__name__)


class OpenAIHelper:
    """A wrapper for the openai python library"""

    # see here: https://platform.openai.com/docs/models/
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_301 = "gpt-3.5-turbo-0301"
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_0314 = "gpt-4-0314"
    GPT_4_32K_0314 = "gpt-4-32k-0314"
    GPT_DEFAULT = GPT_3_5

    GPT_ALL = [
        GPT_3_5,
        GPT_3_5_301,
        GPT_4,
        GPT_4_0314,
        # GPT_4_32K,  # Documented in API docs but not supported. Uncomment when implemented.
        # GPT_4_32K_0314,  # Documented in API docs but not supported. Uncomment when implemented.
    ]

    GPT_3_5_MAX_TOKENS = 4_096
    GPT_4_MAX_TOKENS = 8_192
    GPT_4_32K_MAX_TOKENS = 32_768

    def __init__(self, model: str, payload: List[Dict], stream=False):
        self._model = model
        self._payload = payload
        self._stream = stream

    def send(self) -> requests.Response:
        """Sends message(s) to openai

        :return: The response string from openai
        """
        logger.info("Sending message to openai")
        self._set_api_key()

        key = os.environ["OPENAI_API_KEY"]
        response = self._post_request(key=key)

        return response

    def is_valid_api_key(self, key) -> bool:
        """Sends a POST request to the Openai API.
        We expect a return of True if we have a valid key and false if not.
        """
        response = self._post_request(key=key)
        is_valid = True if response.status_code == 200 else False

        return is_valid

    def _set_api_key(self) -> None:
        if "OPENAI_API_KEY" not in os.environ:
            logger.info("Exporting API key to environment variable")

            # get api key from file
            bash_script_path = os.path.join(os.path.expanduser("~"), ".gptcli/keys/openai")
            with open(bash_script_path, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.read()
        else:
            logger.info("API key already in environment variable")

    def _post_request(self, key: str) -> requests.Response:
        logger.info("POSTing request to openai API")
        messages = self.payload

        request_url = "https://api.openai.com/v1/chat/completions"
        request_headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        request_body = {
            "model": self.model,
            "stream": self.stream,
            "messages": messages,
        }

        response = None  # return None rather than uninitiated variable
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
            logger.exception("This likely manual user intervention")  # for when the user decides to exit during a POST

        # Http error codes reference: https://platform.openai.com/docs/guides/error-codes/api-errors
        if response is not None:  # response retrieved
            code = response.status_code
            match code:
                case _ if code >= 400 and code < 500:
                    match code:
                        case HTTPStatus.UNAUTHORIZED.value:  # 401
                            logger.warning("Received UNAUTHORIZED client error")
                        case HTTPStatus.NOT_FOUND.value:  # 404
                            logger.warning("Received NOT_FOUND client error")
                        case HTTPStatus.TOO_MANY_REQUESTS.value:  # 429
                            logger.warning("Received TOO_MANY_REQUESTS client error")
                        case _:
                            logger.warning("Received unexpected client error")
                case _ if code >= 500 and code < 600:
                    match code:
                        case HTTPStatus.SERVICE_UNAVAILABLE.value:  # 503
                            logger.warning("Received SERVICE_UNAVAILABLE server error")
                        case _:
                            logger.warning("Received unexpected server error")
                case _:
                    logger.warning("Response code not recongnized!")

            # response = Response()

        else:
            logger.warning("Response not retrieved. Replying with dummy Response object")
            # response = Response()

        return response

    @property
    def model(self) -> str:
        return self._model

    @property
    def payload(self) -> List[Dict]:
        return self._payload

    @property
    def stream(self) -> bool:
        return self._stream
