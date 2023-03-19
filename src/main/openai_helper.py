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

    DEFAULT_ENGINE = "gpt-4-0314"
    MAX_TOKENS = 8_192  # The limit as defined by openai docs

    openai.api_key = os.getenv("OPENAI_API_KEY")

    def __init__(self, model: str, user_input: str):
        self.model = model
        self.user_input = user_input

    def send(self) -> str:
        """
        Sends message(s) to openai

        :return: The response from openai
        """
        logger.info("Sending message to openai")
        chat_completion = self._create_chat_completion()
        content = self._retrieve_chat_completion_content(chat_completion)

        return content

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
