"""Contains a wrapper for the openai SDK"""

import json
import logging
import os
from http import HTTPStatus
from logging import Logger

import requests
from requests import Response, Session
from requests.exceptions import ReadTimeout

from gptcli.definitions import GPTCLI_KEYS_OPENAI, OPENAI_API_KEY
from gptcli.src.decorators import allow_graceful_stream_exit
from gptcli.src.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


def _export_api_key_to_environment_variable() -> None:
    if OPENAI_API_KEY not in os.environ:
        logger.info("Exporting API key to environment variable")

        # get api key from file
        with open(GPTCLI_KEYS_OPENAI, "r", encoding="utf8") as filepointer:
            os.environ[OPENAI_API_KEY] = filepointer.read()
    else:
        logger.info("API key already in environment variable")


def _check_for_http_errors(response: Response | None) -> None:
    logger.info("Checking for http errors")

    # Http error codes reference: https://platform.openai.com/docs/guides/error-codes/api-errors
    if response:  # response retrieved
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
                    logger.warning("Response code not recognized!")
            error = json.loads(response.content)["error"]
            log_message = ":".join(
                [
                    error["message"],
                    error["type"],
                    error["code"],
                ]
            )
            logger.warning(log_message)

    if not response:
        raise ValueError("Response not retrieved from API call.")


class Chat:
    """This class contains the methods used for a continuous chat session with the API.

    The difference between this class and SingleExchange is the Object type being returned by the methods,
    and when the received bytes from the API are printed. In Chat, the objects returned are:

    - Message
    - Messages

    This is because, unlike SingleExchange, no further processing is done outside this class.
    To understand the type of processing being done in SingleExchange, please read its docstring.
    """

    def __init__(self, model: str, messages: Messages, stream=False):
        self._model: str = model
        self._messages: list[dict] = [message.to_dict_reduced_context() for message in messages]
        self._stream: bool = stream

    def send(self) -> Message:
        """Sends message(s) to openai

        :return: The requests.Response object sent from the server. None, if request was invalid.
        """
        logger.info("Sending message to openai")

        _export_api_key_to_environment_variable()
        key: str = os.environ[OPENAI_API_KEY]
        message: Message = self._build_and_execute_post_request(key=key)

        return message

    def _build_and_execute_post_request(self, key: str) -> Message:
        logger.info("POSTing request to openai API")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        body = {
            "model": self._model,
            "stream": self._stream,
            "messages": self._messages,
        }

        message: Message
        try:
            message = (
                self._post_request(url=url, headers=headers, body=body)
                if not self._stream
                else self._post_request_stream(url=url, headers=headers, body=body)
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

        return message

    def _post_request(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message:
        logger.info("Posting request to openai api")

        response: Response = requests.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30)
        _check_for_http_errors(response=response)
        content: str = json.loads(response.content.decode(encoding="utf8"))["choices"][0]["message"]["content"]
        print(content)
        message = MessageFactory.create_reply_message(role="assistant", content=content, model=self._model)

        return message

    @allow_graceful_stream_exit
    def _post_request_stream(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message:
        logger.info("Posting request to openai api - stream mode")

        content: str = ""
        session: Session = requests.Session()
        with session.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30) as response:
            _check_for_http_errors(response=response)
            for line in response.iter_lines(decode_unicode=True):
                if len(line) == 0:  # iter_lines is giving an extra chunk that is empty; skip it, TODO: find out why
                    continue
                elif "content" in line:  # not all chunks have content we want to print
                    chunk: str = json.loads(line.removeprefix("data: "))["choices"][0]["delta"]["content"]
                    print(chunk, end="", flush=True)
                    content = "".join([content, chunk])
        print("")

        message: Message = MessageFactory.create_reply_message(role="assistant", content=content, model=self._model)

        return message


class SingleExchange:
    """This class contains the methods used for a single message exchange between the user and the API.

    The difference between this class and SingleExchange is the Object type being returned by the methods,
    and when the received bytes from the API are printed. In SingleExchange, the object(s) returned is(are):

    - requests.Response

    This is because, unlike Chat, further processing is done outside this class.
    This is necessary if we want the 'output' flag of GPTCLI to work.
    """

    def __init__(self, model: str, messages: Messages, stream=False):
        self._model: str = model
        self._messages: list[dict] = [message.to_dict_reduced_context() for message in messages]
        self._stream: bool = stream

    def send(self) -> Response:
        """Sends message(s) to openai

        :return: The requests.Response object sent from the server. None, if request was invalid.
        """
        logger.info("Sending message to openai")

        _export_api_key_to_environment_variable()
        key: str = os.environ[OPENAI_API_KEY]
        response: Response = self._build_and_execute_post_request(key=key)

        return response

    def is_valid_api_key(self, key: str) -> bool:
        """Sends a POST request to the Openai API.
        We expect a return of True if we have a valid key and false if not.
        """
        logger.info("Checking if we have a valid API key")

        try:
            response: Response = self._build_and_execute_post_request(key=key)
        except ValueError:
            return False

        return False if response is None else True

    def _build_and_execute_post_request(self, key: str) -> Response:
        logger.info("POSTing request to openai API")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        body = {
            "model": self._model,
            "stream": self._stream,
            "messages": self._messages,
        }

        response: Response
        try:
            response = self._post_request(url=url, headers=headers, body=body)
        # Python errors reference: https://platform.openai.com/docs/guides/error-codes/python-library-error-types
        except ReadTimeout:
            logger.exception("The server did not send any data in the allotted amount of time")
        except TimeoutError:
            logger.exception("This is likely an issue with the API")
        except requests.exceptions.ConnectionError:
            logger.exception("This is likely a local issue")
        except KeyboardInterrupt:  # when the user decides to exit during a POST
            logger.exception("This is likely manual user intervention")

        return response

    def _post_request(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Response:
        logger.info("Posting request to openai api")

        response: Response = requests.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30)
        _check_for_http_errors(response=response)

        return response
