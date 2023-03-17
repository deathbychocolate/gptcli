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

    def dictionary(self):
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
    def create_message(role: str, content: str):
        """
        Creates a message

        :param role: The role of the message
        :param content: The content of the message
        :return: A message
        """
        return Message(role, content).dictionary()


class OpenAIWrapper:
    """
    A wrapper for the openai python library
    """

    DEFAULT_ENGINE = "gpt-4-0314"
    MAX_TOKENS = 8_192  # The limit as defined by openai docs

    openai.api_key = os.getenv("OPENAI_API_KEY")

    def __init__(self, model: str, question: str):
        """
        Constructor
        """
        self.model = model
        self.question = question

    def send(self):
        """
        Sends message(s) to openai

        :return: The response from openai
        """
        logger.info("Sending message to openai")
        messages = self._build_messages(self.question)
        response = openai.ChatCompletion.create(model=self.model, messages=messages)
        reply = response["choices"][0]["message"]["content"]
        logger.info("Openai replied with: %s", reply)

        return reply

    def _build_messages(self, question: str) -> list:
        """
        Builds messages to pass to openai
        TODO: it currently handles only one message, it should handle multiple

        :param messages: The question to use
        :return: A list representation of the question to ask openai
        """
        logger.info("Building messages to pass to openai")
        messages = [MessageFactory.create_message("user", question)]
        logger.info("Messages built: %s", messages)

        return messages
