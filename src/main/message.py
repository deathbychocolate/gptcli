"""Will handle messages to and from Openai's API"""

import logging
import tiktoken

from src.main.api_helper import OpenAIHelper

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
        return self._num_tokens_from_message(self.to_dictionary())

    def _num_tokens_from_message(self, message, model="gpt-3.5-turbo-0301"):
        # Algorithm retrieved from Deep Dive section: https://platform.openai.com/docs/guides/chat/introduction
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

    def to_dictionary(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
        }


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
