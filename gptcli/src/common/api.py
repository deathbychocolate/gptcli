"""This file holds all the code that makes direct calls to the desired AI API.

In order to make a call, it has to do 3 steps in order:
1 - Make preparations to send a payload (message/messages) to the API.
2 - Send the payload.
3 - Receive a payload back (message/messages as a reply) from the API.
"""

import itertools
import json
import logging
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
from gptcli.src.common.constants import BLU, GRN, MGA, MISTRAL, OPENAI, RST
from gptcli.src.common.decorators import allow_graceful_stream_exit
from gptcli.src.common.message import Message, MessageFactory, Messages

logger: Logger = logging.getLogger(__name__)


class Spinner:

    _FRAMES: tuple[str, ...] = ("⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓")

    def __init__(self, interval: float = 0.1, label: str = "") -> None:
        """Simulates a thinking animation when we send requests to an AI provider's AI model.

        Args:
            interval (float, optional): Time interval that controls animation speed; lower is faster. Defaults to 0.1s.
            label (str, optional): Label displayed next to the spinner character. Defaults to empty string.
        """
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval = interval
        self.label: str = label

    def _animate(self) -> None:
        printed: bool = False
        for c in itertools.cycle(self._FRAMES):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\r{BLU}{c}{RST} {self.label}")
            sys.stdout.flush()
            printed = True
            time.sleep(self._interval)

        if printed:
            self._on_complete()

    def _on_complete(self) -> None:
        """Clears the spinner line with a carriage return."""
        sys.stdout.write("\r")

    def __enter__(self) -> Self:
        self._stop.clear()
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


class SpinnerProgress(Spinner):
    """Spinner that displays file processing progress."""

    def __init__(self, total: int, interval: float = 0.1, label: str = "Processing") -> None:
        """Initialize with a total file count for progress display.

        Args:
            total (int): Total number of files to process.
            interval (float): Animation speed interval. Defaults to 0.1s.
            label (str): Label prefix for the progress display. Defaults to "Processing".
        """
        super().__init__(interval=interval, label=f"{label}: 0/{total} files")
        self._total: int = total
        self._count: int = 0
        self._label_prefix: str = label

    def advance(self) -> None:
        """Increment the progress counter and update the label."""
        self._count += 1
        self.label = f"{self._label_prefix}: {self._count}/{self._total} files"

    def _on_complete(self) -> None:
        sys.stdout.write(f"\r{GRN}✔{RST} {self.label}\n")


class SpinnerRecognizing(Spinner):
    """Spinner displayed during OCR recognition; shows a checkmark on completion."""

    def __init__(self, interval: float = 0.1, label: str = "Recognizing") -> None:
        super().__init__(interval=interval, label=label)

    def _on_complete(self) -> None:
        sys.stdout.write(f"\r{GRN}✔{RST} {self.label}\n")


class SpinnerThinking(Spinner):
    """Spinner displayed while waiting for an AI response; clears silently on completion."""

    def __init__(self, interval: float = 0.1, label: str = "Thinking") -> None:
        super().__init__(interval=interval, label=label)


recognizing_spinner: SpinnerRecognizing = SpinnerRecognizing()
thinking_spinner: SpinnerThinking = SpinnerThinking()


class EndpointHelper:
    """Abstracts the constants used in Chat and SingleExchange depending on the provider name."""

    def __init__(self, provider: str, api_key: str = "") -> None:
        self._provider: str = provider
        self._resolved_api_key: str = api_key
        self._api_key_env_var: str = ""
        self._api_key_file: str = ""
        self._url: str = ""
        self._message_factory: MessageFactory = MessageFactory(provider="dummy")

        if provider == MISTRAL:
            self._api_key_env_var = MISTRAL_API_KEY
            self._api_key_file = GPTCLI_PROVIDER_MISTRAL_KEY_FILE
            self._url = "https://api.mistral.ai/v1/chat/completions"
            self._message_factory = MessageFactory(provider=provider)
        elif provider == OPENAI:
            self._api_key_env_var = OPENAI_API_KEY
            self._api_key_file = GPTCLI_PROVIDER_OPENAI_KEY_FILE
            self._url = "https://api.openai.com/v1/chat/completions"
            self._message_factory = MessageFactory(provider=provider)
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

    def _resolve_api_key(self) -> str:
        """Resolve the API key, preferring the directly provided key over file-based fallback.

        Returns:
            str: The resolved API key.
        """
        if self._resolved_api_key:
            return self._resolved_api_key

        logger.info("API key not provided directly, reading from file.")
        with open(self._api_key_file, "r", encoding="utf8") as fp:
            self._resolved_api_key = fp.read()
        return self._resolved_api_key

    def _check_for_http_errors(self, response: Response | None) -> bool:
        """Check for common HTTP errors when calling the provider endpoint.

        Detail:
            This function accepts a response object generated from the 'requests' package.
            It then runs a pattern matching check against errors as documented by the provider and errors
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

    def __init__(self, provider: str, model: str, messages: Messages, stream: bool = False, api_key: str = "") -> None:
        """Used for multiple (>1) message-reply transactions.

        Args:
            model (str): The model we wish to use, for example `o1`, `o3`, or `mistral-large`.
            messages (Messages): The messages created during a chat session.
            stream (bool, optional): Enables stream mode for chat session. Defaults to False.
            api_key (str, optional): The API key for authentication. Defaults to "".
        """
        super().__init__(provider=provider, api_key=api_key)
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

    def send(self) -> Message | None:
        """Sends message(s) to API endpoint.

        Returns:
            Message | None: A Message object derived from the object sent by the server, or None on failure.
        """
        logger.info("Sending message to API endpoint.")

        key: str = self._resolve_api_key()
        message: Message | None = self._send_request(key=key)

        if message is None:
            logger.warning("Unable to retrieve message from post request. This is likely a server issue.")

        return message

    def _send_request(self, key: str) -> Message | None:
        logger.info("POSTing request to provider API.")

        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + key,
        }
        body = {
            "model": self._model,
            "stream": self._stream,
            "messages": [m.to_dict_reduced_context() for m in sorted(self._messages, key=lambda m: not m.is_system)],
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

    def _post_request(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message | None:
        logger.info("Posting request to provider API.")

        response: Response = requests.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30)
        found_errors: bool = self._check_for_http_errors(response=response)
        if found_errors:
            return None

        content: str = json.loads(response.content.decode(encoding="utf8"))["choices"][0]["message"]["content"]
        print(f"{MGA}>>>{RST} {content}")
        message = self._message_factory.reply_message(content=content, model=self._model)

        return message

    @allow_graceful_stream_exit
    def _post_request_stream(self, url: str, headers: dict[str, str], body: dict[str, object]) -> Message | None:
        logger.info("Posting request to provider API - stream mode.")

        content: str = ""
        session: Session = requests.Session()

        with thinking_spinner:
            response = session.post(url=url, headers=headers, stream=self._stream, json=body, timeout=60)

        found_errors: bool = self._check_for_http_errors(response=response)
        if found_errors:
            return None

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

    def __init__(self, provider: str, model: str, messages: Messages, stream: bool = False, api_key: str = "") -> None:
        super().__init__(provider=provider, api_key=api_key)
        self._model: str = model
        self._messages: list[dict[str, str]] = [message.to_dict_reduced_context() for message in messages]
        self._stream: bool = stream

    def send(self) -> Response:
        """Sends message(s) to the provider API.

        Returns:
            Response: The response object sent from the server. None, if request was invalid.
        """
        logger.info("Sending message to provider API.")

        key: str = self._resolve_api_key()
        response: Response = self._send_request(key=key)

        return response

    def is_valid_api_key(self, key: str) -> bool:
        """Sends a POST request to the provider API.
        We expect a return of True if we have a valid key and false if not.

        Args:
            key (str): The API key used to communicate with the LLMs.

        Returns:
            bool: True if we do not get a ValueError, otherwise False.
        """
        logger.info("Checking if we have a valid API key")

        try:
            response: Response = self._send_request(key=key)
        except ValueError:
            return False

        return False if (not response or not response.ok) else True

    def _send_request(self, key: str) -> Response:
        logger.info("POSTing request to provider API.")

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
        logger.info("Posting request to provider API.")

        response: Response = requests.post(url=url, headers=headers, stream=self._stream, json=body, timeout=30)
        self._check_for_http_errors(response=response)

        return response
