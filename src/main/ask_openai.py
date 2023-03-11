"""
Contains a wrapper for the openai SDK
"""
import os
import openai


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


class AskOpenAI:
    """
    A wrapper for the openai python library
    """

    DEFAULT_ENGINE = "gpt-3.5-turbo"
    MAX_TOKENS = 4096  # The limit as defined by openai docs

    openai.api_key = os.getenv("OPENAI_API_KEY")

    def __init__(self, model: str, question: str):
        """
        Constructor
        """
        self.model = model
        self.question = question

    def ask(self):
        """
        Asks openai a question

        :param model: The model to use
        :param messages: The messages to use
        :return: The response from openai
        """
        messages = self._build_messages(self.question)
        response = openai.ChatCompletion.create(model=self.model, messages=messages)
        reply = response["choices"][0]["message"]["content"]

        return reply

    def _build_messages(self, question: str) -> list:
        """
        Builds messages to pass to openai
        TODO: it currently handles only one message, it should handle multiple

        :param messages: The question to use
        :return: A list representation of the question to ask openai
        """
        messages = [MessageFactory.create_message("user", question)]

        return messages
