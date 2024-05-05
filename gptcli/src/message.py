"""Will handle messages to and from Openai's API"""

import logging
from typing import Dict, List

import tiktoken

from gptcli.src.api_helper import OpenAIHelper

logger = logging.getLogger(__name__)


class Message:
    """A message can be created by a user or by an API.
    The idea is we need a blueprint to express the message
    contents and metadata to, among other things, count tokens,
    store the message locally as a dictionary/JSON object etc.

    Attributes:
        role (str): The role of the message.
        content (str): The content of the message.
        model (str): The LLM model requested for this message.
        is_reply (bool): False if it is a message sent by the user, and False if it is sent by the external API
        tokens (int): The token count estimated that will be needed to read this message by the OpenAI API.

    Methods:
        number_of_tokens_from_message:
    """

    def __init__(self, role: str, content: str, model: str, is_reply: bool) -> None:
        self._role: str = role
        self._content: str = content
        self._model: str = model
        self._is_reply: bool = is_reply
        self._tokens: int = self.number_of_tokens_from_message()

    def number_of_tokens_from_message(self) -> int:
        """Returns the number of tokens used by a list of messages.

        Keep an eye on this webpage to see if they support newer or different models.
        Please, note that the tokenizer seems to only consider the text of the message,
        and not the roles or names associated with it:
        https://platform.openai.com/tokenizer

        Source of algorithm:
        https://platform.openai.com/docs/guides/text-generation/managing-tokens

        Raises:
            NotImplementedError: Raised when the model requested by the user is not supported by GPTCLI.

        Returns:
            int: The number of tokens required for this message.
        """

        logger.info("Counting tokens for message")
        supported_models = set([*(OpenAIHelper.GPT_3_5_ALL), *(OpenAIHelper.GPT_4_ALL)])
        if self._model not in supported_models:
            raise NotImplementedError(f"num_tokens_from_message() is not presently implemented for {self._model}.")
        else:
            try:
                encoding = tiktoken.encoding_for_model(self._model)
            except KeyError as exception:
                logger.info("It seems the encoding for '%s' was not found. Switching to 'cl100k_base'.", self._model)
                logger.exception(exception)
                encoding = tiktoken.get_encoding("cl100k_base")

            num_tokens: int = 0
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += len(encoding.encode(self._content))
            if self._role == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
            if self._is_reply:
                num_tokens += 2  # every reply is primed with <im_start>assistant

            return num_tokens

    def to_dictionary_reduced_context(self) -> dict:
        """Use this lightweight version when sending messages to API endpoints.
        If we send less, we save tokens.

        Returns:
            dict: A lightweight dictionary representation of the Messsage class.
        """

        return {
            "role": self._role,
            "content": self._content,
        }

    def to_dictionary_full_context(self) -> dict:
        """Use this version when storing messages locally in your machine.
        When storing messages locally, we want the full context for each message.

        Returns:
            dict: A complete dictionary representation of the Messsage class.
        """

        return {
            "role": self._role,
            "content": self._content,
            "model": self._model,
            "is_reply": self._is_reply,
            "tokens": self._tokens,
        }

    @property
    def tokens(self) -> int:
        return self._tokens


class MessageFactory:
    """A factory for creating messages"""

    @staticmethod
    def create_user_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content

        Args:
            role (str): The role dersignated by the user at the start (user, mathmatician, pilot etc)
            content (str): The content of the message body
            model (str): The LLM used for this message

        Returns:
            Message: A Message object specially suited for user generated messages
        """
        return Message(role=role, content=content, model=model, is_reply=False)

    @staticmethod
    def create_reply_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content

        Args:
            role (str): The role dersignated by the user at the start (user, mathmatician, pilot etc)
            content (str): The content of the message body
            model (str): The LLM used for this message

        Returns:
            Message: A Message object specially suited for user generated messages
        """
        return Message(role=role, content=content, model=model, is_reply=True)


class Messages:
    """A class to represent the collection of Message objects.

    It fulfills the need of custom functionalities
    that are not offered by Python dicitionaries or lists.
    """

    def __init__(self) -> None:
        self._messages: List[Message] = list()
        self._tokens = self._count_tokens()

    def add_message(self, message: Message) -> None:
        """Add a Message object to Messages.

        Args:
            message (Message): A simple Message object.
        """
        logger.info("Adding message %s to messages.", message.to_dictionary_reduced_context())
        if message is None:
            logger.warning("Tried to add message of class NoneType")
            logger.warning("Skipping message")
        else:
            self._messages.append(message)
            self._tokens += message.tokens

    def _count_tokens(self) -> None:
        logger.info("Counting total number of used in messages.")
        count = 0
        for message in self.messages:
            count = count + message.tokens
        return count

    @property
    def messages(self) -> List[Dict]:
        return self._messages

    @property
    def tokens(self) -> int:
        return self._tokens
