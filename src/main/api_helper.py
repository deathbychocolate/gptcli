"""Contains a wrapper for the openai SDK
"""
import os
import logging
from typing import List, Dict

import requests
from requests.exceptions import ReadTimeout
import tiktoken


logger = logging.getLogger(__name__)


class Message:
    """A message that will be fed to openai

    Attributes:
        role: The role of the message
        content: The content of the message
    """

    def __init__(self, role: str, content: str):
        self._role = role
        self._content = content
        self._tokens = self._count_tokens()


    def _count_tokens(self) -> int:
        return self._num_tokens_from_message(self.dictionary())

    def _num_tokens_from_message(self, message, model="gpt-3.5-turbo-0301"):
        # See: https://platform.openai.com/docs/guides/chat/introduction
        # See: https://github.com/openai/openai-python/blob/main/chatml.md
        encoding = tiktoken.encoding_for_model(model)
        number_of_tokens = -1
        if model == OpenAIHelper.GPT_3_5_301:
            number_of_tokens = 0
            number_of_tokens += 4
            for key, value in message.items():
                number_of_tokens += len(encoding.encode(value))
                if key == "name":
                    number_of_tokens += -1
            number_of_tokens += 2
        else:
            logger.warning("Model '%s' not supported for token count", model)

        return number_of_tokens

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, content) -> None:
        if not isinstance(content, str):
            raise ValueError("Content must be a string.")
        self._content = content

    @property
    def tokens(self) -> int:
        return self._tokens

    def dictionary(self) -> dict:
        """Returns a dictionary representation of the message"""
        return {"role": self.role, "content": self.content}


class MessageFactory:
    """A factory for creating messages"""

    @staticmethod
    def create_message(role: str, content: str) -> Message:
        """Creates a message, you may specify the role and the content

        :param role: The role of the message
        :param content: The content of the message
        :return: A message object
        """
        return Message(role, content)


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
        # GPT_4_32K, Documented in API docs but not supported. Uncomment when implemented.
        GPT_4_0314,
        # GPT_4_32K_0314, Documented in API docs but not supported. Uncomment when implemented.
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
        # TODO: FEATURE: handle all error codes here: https://platform.openai.com/docs/guides/error-codes/api-errors
        except ReadTimeout:
            logger.exception("ReadTimeout error detected")
        except TimeoutError:
            logger.exception("Timeout error detected")
        except requests.exceptions.ConnectionError:
            logger.exception("It seems you lack an internet connection, please manually resolve the issue")
        except KeyboardInterrupt:
            logger.exception("Keyboard intterupt detected")  # for when the user decides to exit during a POST
        # Consider susing sys.exc_info()
        # import sys

        # def call_function(func):
        #     try:
        #         func()
        #     except Exception as e:
        #         ex_type, ex_value, ex_traceback = sys.exc_info()
        #         if ex_type.__module__ == "your_target_module":
        #             print("Caught an exception from the target module:", ex_type, ex_value)
        #         else:
        #             print("Caught an exception from a different module:", ex_type, ex_value)

        # # Example of calling a function that may raise an exception and checking if it's from the target module

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
