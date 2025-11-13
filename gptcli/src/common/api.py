"""This file holds all the code that makes direct calls to the desired AI API.

In order to make a call, it has to do 3 steps in order:
1 - Make preparations to send a payload (message/messages) to the API.
2 - Send the payload.
3 - Receive a payload back (message/messages as a reply) from the API.
"""

import itertools
import json
import logging
import os
import sys
import threading
import time
from http import HTTPStatus
from logging import Logger
from types import TracebackType
from typing import Self, Type

import requests
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI
from requests import Response, Session
from requests.exceptions import ReadTimeout

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    MISTRAL_API_KEY,
    OPENAI_API_KEY,
)
from gptcli.src.common.constants import MGA, MISTRAL, OPENAI, RST
from gptcli.src.common.decorators import allow_graceful_stream_exit
from gptcli.src.common.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


class SpinnerThinking:

    def __init__(self, interval: float = 0.1) -> None:
        """Simulates a thinking animation when we send requests to an AI provider's AI model.

        Args:
            interval (float, optional): Time interval that controls animation speed; lower is faster. Defaults to 0.1s.
        """
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval = interval

    def _animate(self) -> None:
        for c in itertools.cycle(["-", "\\", "|", "/"]):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\rThinking {c}")
            sys.stdout.flush()
            time.sleep(self._interval)
        sys.stdout.write("\r")

    def __enter__(self) -> Self:
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._stop.set()
        if self._thread:
            self._thread.join()
        return None  # let errors propagate


thinking_spinner: SpinnerThinking = SpinnerThinking()


class EndpointHelper:
    """Abstracts the constants used in Chat and SingleExchange depending on the provider name."""

    def __init__(self, provider: str) -> None:
        self._provider: str = provider
        self._api_key: str = ""
        self._api_key_file: str = ""
        self._url: str = ""
        self._message_factory: MessageFactory = MessageFactory(provider="dummy")

        if provider == MISTRAL:
            self._api_key = MISTRAL_API_KEY
            self._api_key_file = GPTCLI_PROVIDER_MISTRAL_KEY_FILE
            self._url = "https://api.mistral.ai/v1/chat/completions"
            self._message_factory = MessageFactory(provider=provider)
        elif provider == OPENAI:
            self._api_key = OPENAI_API_KEY
            self._api_key_file = GPTCLI_PROVIDER_OPENAI_KEY_FILE
            self._url = "https://api.openai.com/v1/chat/completions"
            self._message_factory = MessageFactory(provider=provider)
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

    def _export_api_key_to_environment_variable(self) -> None:
        if self._api_key not in os.environ:
            logger.info("Exporting API key to environment variable")

            # get api key from file
            with open(self._api_key_file, "r", encoding="utf8") as fp:
                os.environ[self._api_key] = fp.read()
        else:
            logger.info("API key already in environment variable")

    def _check_for_http_errors(self, response: Response | None) -> bool:
        """A function that checks for common HTTP errors when calling the OpenAI endpoint.

        Detail:
            This function accepts a response object generated from the 'requests' package.
            It then runs a pattern matching check against errors as documented by OpenAI and errors
            that we ourselves have found.

        Args:
            response (Response | None): The response that was received from the API endpoint.

        Raises:
            ValueError: Raised when response is 'None'

        Returns:
            bool: True if errors were found. False otherwise.
        """
        logger.info("Checking for HTTP errors")

        # Http error codes reference (mistral): https://docs.mistral.ai/api/
        # Http error codes reference (openai): https://platform.openai.com/docs/guides/error-codes/api-errors
        if response is not None:  # response retrieved
            code: int = response.status_code
            if code >= 400:
                match code:
                    case HTTPStatus.UNAUTHORIZED.value:  # 401
                        logger.warning("Received UNAUTHORIZED client error")
                    case HTTPStatus.NOT_FOUND.value:  # 404
                        logger.warning("Received NOT_FOUND client error")
                    case HTTPStatus.UNPROCESSABLE_ENTITY.value:  # 422 (mistral)
                        logger.warning("Received UNPROCESSABLE_ENTITY client error")
                    case HTTPStatus.TOO_MANY_REQUESTS.value:  # 429
                        logger.warning("Received TOO_MANY_REQUESTS client error")
                    case HTTPStatus.SERVICE_UNAVAILABLE.value:  # 503
                        logger.warning("Received SERVICE_UNAVAILABLE server error")
                    case _ if 400 <= code < 500:
                        logger.warning("Received unexpected client error")
                    case _ if 500 <= code < 600:
                        logger.warning("Received unexpected server error")
                    case _ if code >= 600:
                        logger.warning("Response code not recognized!")

                if self._provider == MISTRAL:
                    error = json.loads(response.content)
                elif self._provider == OPENAI:
                    error = json.loads(response.content)["error"]
                else:
                    raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

                log_message = ":".join(v for v in error.values() if isinstance(v, str))
                print(log_message)
                logger.warning(log_message)

                return True

        if response is None:
            raise ValueError("Response not retrieved from API call.")

        return False


class Chat(EndpointHelper):
    """This class contains the methods used for a continuous chat session with the API.

    The difference between this class and SingleExchange is the Object type being returned by the methods,
    and when the received bytes from the API are printed. In Chat, the objects returned are:

    - Message
    - Messages

    This is because, unlike SingleExchange, no further processing is done outside this class.
    To understand the type of processing being done in SingleExchange, please read its docstring.
    """

    def __init__(self, provider: str, model: str, messages: Messages, stream: bool = False) -> None:
        """Used for multiple (>1) message-reply transactions.

        Args:
            model (str): The model we wish to use, for example `o1`, `o3`, or `mistral-large`.
            messages (Messages): The messages created during a chat session.
            stream (bool, optional): Enables stream mode for chat session. Defaults to False.
        """
        super().__init__(provider=provider)
        self._model: str = model
        self._messages: Messages = messages
        self._stream: bool = stream

    @property
    def messages(self) -> Messages:
        """The messages to pass to send to the API."""
        return self._messages

    @messages.setter
    def messages(self, messages: Messages) -> None:
        """Set the value for messages."""
        if not isinstance(messages, Messages):
            raise ValueError(f"Parameter 'messages' only accepts Messages values and not '{type(messages)}'.")
        self._messages = messages

    def send(self) -> Message:
        """Sends message(s) to API endpoint.

        Returns:
            Message: A Message object derived from the object sent by the server.
        """
        logger.info("Sending message to API endpoint.")

        self._export_api_key_to_environment_variable()
        key: str = os.environ[self._api_key]
        message: Message | None = self._build_and_execute_post_request(key=key)

        if message is None:
            logger.warning("Unable to retrieve message from post request. This is likely a server issue.")
            logger.warning("Creating empty dummy message instead.")
            message = self._message_factory.reply_message(content="", model=self._model)

        return message

    def _build_and_execute_post_request(self, key: str) -> Message | None:
        logger.info("POSTing request to OpenAI's API.")

        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        body = {
            "model": self._model,
            "stream": self._stream,
            "messages": [message.to_dict_reduced_context() for message in self._messages],
        }

        message: Message | None = None
        try:
            message = (
                self._post_request(url=self._url, headers=headers, body=body)
                if not self._stream
                else self._post_request_stream(url=self._url, headers=headers, body=body)
            )
        # Python errors reference: https://platform.openai.com/docs/guides/error-codes/python-library-error-types
        except ReadTimeout:
            logger.exception("The server did not send any data in the allotted amount of time.")
        except TimeoutError:
            logger.exception("Timeout expired. This is likely an issue with the API.")
        except requests.exceptions.ConnectionError:
            logger.exception("A Connection error occurred. This is likely a local issue.")
        except KeyboardInterrupt:
            logger.exception("Program interrupted by user. This is likely caused by an interrupt signal.")
        except Exception:
            logger.exception("An unknown error has occurred. This is likely a server issue.")

        return message

    def _post_request(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message:
        logger.info("Posting request to openai api")

        response: Response = requests.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30)
        self._check_for_http_errors(response=response)
        content: str = json.loads(response.content.decode(encoding="utf8"))["choices"][0]["message"]["content"]
        print(f"{MGA}>>>{RST} {content}")
        message = self._message_factory.reply_message(content=content, model=self._model)

        return message

    @allow_graceful_stream_exit
    def _post_request_stream(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message:
        logger.info("Posting request to openai api - stream mode")

        content: str = ""
        session: Session = requests.Session()

        with thinking_spinner:
            response = session.post(url=url, headers=headers, stream=self._stream, json=body, timeout=60)

        found_errors: bool = self._check_for_http_errors(response=response)
        if not found_errors:  # don't bother printing
            print_formatted_text(ANSI(f"{MGA}>>>{RST} "), end="")
            for line in response.iter_lines(decode_unicode=True):
                if len(line) == 0:  # iter_lines has an extra chunk that is empty; skip it
                    continue
                elif "content" in line:  # not all chunks have content we want to print
                    chunk: str = json.loads(line.removeprefix("data: "))["choices"][0]["delta"]["content"]
                    print(chunk, end="", flush=True)
                    content = "".join([content, chunk])
            print("")

        message: Message = self._message_factory.reply_message(content=content, model=self._model)

        return message


class SingleExchange(EndpointHelper):
    """This class contains the methods used for a single message exchange between the user and the API.

    The difference between this class and SingleExchange is the Object type being returned by the methods,
    and when the received bytes from the API are printed. In SingleExchange, the object(s) returned is(are):

    - requests.Response

    This is because, unlike Chat, further processing is done outside this class.
    This is necessary if we want the 'output' flag of GPTCLI to work.
    """

    def __init__(self, provider: str, model: str, messages: Messages, stream: bool = False) -> None:
        super().__init__(provider=provider)
        self._model: str = model
        self._messages: list[dict[str, str]] = [message.to_dict_reduced_context() for message in messages]
        self._stream: bool = stream

    def send(self) -> Response:
        """Sends message(s) to openai.

        Returns:
            Response: The response object sent from the server. None, if request was invalid.
        """
        logger.info("Sending message to openai")

        self._export_api_key_to_environment_variable()
        key: str = os.environ[self._api_key]
        response: Response = self._build_and_execute_post_request(key=key)

        return response

    def is_valid_api_key(self, key: str) -> bool:
        """Sends a POST request to the Openai API.
        We expect a return of True if we have a valid key and false if not.

        Args:
            key (str): The API key used to communicate with the LLMs.

        Returns:
            bool: True if we do not get a ValueError, otherwise False.
        """
        logger.info("Checking if we have a valid API key")

        try:
            response: Response = self._build_and_execute_post_request(key=key)
        except ValueError:
            return False

        return False if (not response or not response.ok) else True

    def _build_and_execute_post_request(self, key: str) -> Response:
        logger.info("POSTing request to openai API")

        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        body = {
            "model": self._model,
            "stream": self._stream,
            "messages": self._messages,
        }

        response: Response = Response()
        try:
            response = self._post_request(url=self._url, headers=headers, body=body)
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
        self._check_for_http_errors(response=response)

        return response
