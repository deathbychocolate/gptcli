"""
Contains a wrapper for the openai SDK
"""
import os
import logging
import openai


logger = logging.getLogger(__name__)


class Message:
    """
    A message that will be fed to openai

    Attributes:
        role: The role of the message
        content: The content of the message
    """

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    @property
    def dictionary(self) -> dict:
        """
        Returns a dictionary representation of the message

        :return: a dictionary
        """
        return {"role": self.role, "content": self.content}


class MessageFactory:
    """
    A factory for creating messages
    """

    @staticmethod
    def create_message(role: str, content: str) -> Message:
        """
        Creates a message, you may specify the role and the content

        :param role: The role of the message
        :param content: The content of the message
        :return: A message object
        """
        return Message(role, content)


class OpenAIHelper:
    """
    A wrapper for the openai python library
    """

    # see here: https://platform.openai.com/docs/models/
    GPT_3_5 = "gpt-3.5-turbo"
    GPT_3_5_301 = "gpt-3.5-turbo-0301"
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_0314 = "gpt-4-0314"
    GPT_4_32K_0314 = "gpt-4-32k-0314"

    GPT_ALL = [
        GPT_3_5,
        GPT_3_5_301,
        GPT_4,
        GPT_4_32K,
        GPT_4_0314,
        GPT_4_32K_0314,
    ]

    GPT_DEFAULT = GPT_3_5

    GPT_3_5_MAX_TOKENS = 4_096
    GPT_4_MAX_TOKENS = 8_192
    GPT_4_32K_MAX_TOKENS = 32_768

    def __init__(self, model: str, user_input: str):
        self.model = model
        self.user_input = user_input

    def send(self) -> str:
        """
        Sends message(s) to openai

        :return: The response from openai
        """
        logger.info("Sending message to openai")
        self._set_api_key()
        chat_completion = self._create_chat_completion()
        content = self._retrieve_chat_completion_content(chat_completion)

        return content

    def _set_api_key(self) -> None:
        if "OPENAI_API_KEY" not in os.environ:
            logger.info("Exporting API key to environment variable")

            # get api key from file
            bash_script_path = os.path.join(os.path.expanduser("~"), ".gptcli/keys/openai")
            with open(bash_script_path, "r", encoding="utf8") as filepointer:
                os.environ["OPENAI_API_KEY"] = filepointer.read()

            # get env variable
            openai.api_key = os.getenv("OPENAI_API_KEY", "no api key found")
        else:
            logger.info("API key already set")

    def _create_chat_completion(self) -> dict:
        logger.info("Creating chat completion")
        messages = self._build_messages(self.user_input)
        chat_completion = openai.ChatCompletion.create(model=self.model, messages=messages)

        return chat_completion

    def _retrieve_chat_completion_content(self, chat_completion: dict) -> str:
        return chat_completion["choices"][0]["message"]["content"]

    def _build_messages(self, user_input: str) -> list:
        # TODO: it currently handles only one message, it should handle multiple
        logger.info("Building messages")
        messages = [MessageFactory.create_message("user", user_input).dictionary]

        return messages

    def _build_message(self, user_input: str) -> list:
        logger.info("Building message")
        message = [MessageFactory.create_message("user", user_input).dictionary]

        return message
