"""Will handle messages to and from Openai's API"""

import logging
from logging import Logger

import tiktoken
from tiktoken import Encoding

from gptcli.src.supported_models import openai

logger: Logger = logging.getLogger(__name__)


class Message:
    """A message can be created by a user or by an API.
    Message serves as a blueprint to express the message
    contents and metadata to (among other things) count tokens,
    store the message locally as a dictionary/JSON object etc.

    Attributes:
        role (str): The role of the entity who created the message (ie: user or assistant [usually])
        content (str): The content of the message that is meant to be read by the LLM.
        model (str): The LLM model requested for this message.
        is_reply (bool): False if it is a message sent by the user, and False if it is sent by the external LLM.
        tokens (int): The token count estimated that will be needed to read this message by the LLM.

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
        if self._model not in openai.values():
            raise NotImplementedError(f"num_tokens_from_message() is not presently implemented for {self._model}.")
        else:
            encoding: Encoding = self.encoding()
            num_tokens: int = 0
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += len(encoding.encode(self._content))
            if self._role == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
            if self._is_reply:
                num_tokens += 2  # every reply is primed with <im_start>assistant

            return num_tokens

    def encoding(self) -> Encoding:
        """Determine the encoding to use for the Message.
        The encoding is derived from the LLM model used, via tiktoken.
        The Openai docs seem to prefer 'cl100k_base' encoding for newer models.
        Which may be why it is used as the fallback encoding type. See the link for more:
        https://platform.openai.com/docs/guides/text-generation/managing-tokens

        Returns:
            Encoding: The encoding of the message, which is the encoding used for the model
        """
        try:
            encoding: Encoding = tiktoken.encoding_for_model(self._model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return encoding

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
    """A factory for creating messages."""

    @staticmethod
    def create_user_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content.

        Args:
            role (str): The role dersignated by the user at the start (user, mathmatician, pilot etc).
            content (str): The content of the message body.
            model (str): The LLM used for this message.

        Returns:
            Message: A Message object specially suited for user generated messages.
        """
        return Message(role=role, content=content, model=model, is_reply=False)

    @staticmethod
    def create_reply_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content.

        Args:
            role (str): The role dersignated by the user at the start (user, mathmatician, pilot etc).
            content (str): The content of the message body.
            model (str): The LLM used for this message.

        Returns:
            Message: A Message object specially suited for user generated messages.
        """
        return Message(role=role, content=content, model=model, is_reply=True)


class Messages:
    """A class to represent the collection of Message objects.

    It fulfills the need of custom functionalities
    that are not offered by Python dicitionaries or lists.
    """

    def __init__(self, messages: list[Message] | None = None) -> None:
        self._messages: list[Message] = messages if messages is not None else list()
        self._tokens = self._count_tokens()

    def add_message(self, message: Message | None) -> None:
        """Add a Message object to Messages.

        Args:
            message (Message): A simple Message object.
        """
        logger.info("Adding Message object to Messages object.")
        if message is None:
            logger.warning("Tried to add message of class NoneType.")
            logger.warning("Skipping message.")
        else:
            self._messages.append(message)
            self._tokens += message.tokens

    def __len__(self) -> int:
        return len(self._messages)

    def _count_tokens(self) -> int:
        logger.info("Counting total number of used in messages.")
        count: int = 0
        for message in self._messages:
            count = count + message.tokens
        return count

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def tokens(self) -> int:
        return self._tokens
