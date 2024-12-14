"""Will handle messages to and from Openai's API"""

import json
import logging
from logging import Logger
from time import time
from typing import ClassVar, Optional, Union
from uuid import uuid4

import tiktoken
from tiktoken import Encoding

from gptcli.src.definitions import openai

logger: Logger = logging.getLogger(__name__)


class Message:
    """A message can be created by a user or by an API.
    Message serves as a blueprint to express the message
    contents and metadata to (among other things) count tokens,
    store the message locally as a dictionary/JSON object etc.

    Attributes:
        created (float): The epoch time of creation; includes the milliseconds.
        uuid (str): The uuid of the message to ID specific Message objects.
        role (str): The role of the entity who created the message (ie: user or assistant [usually])
        content (str): The content of the message that is meant to be read by the LLM.
        model (str): The LLM model associated with this Message.
        is_reply (bool): False if it is a message sent by the user, and True if it is sent by the external LLM.
        tokens (int): The estimated token count that this message will require or has consumed from the user's wallet.
        index (int): The index of the message in the conversation/chat.

    Methods:
        _count_tokens: Counts the number of tokens in a Message.
    """

    index: ClassVar[int] = 0

    def __init__(
        self,
        role: str,
        content: str,
        model: str,
        is_reply: bool,
        created: Optional[float] = None,
        uuid: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> None:
        self._created: float = created if created is not None else time()
        self._uuid: str = uuid if uuid is not None else str(uuid4())
        self._role: str = role
        self._content: str = content
        self._model: str = model
        self._is_reply: bool = is_reply
        self._tokens: int = tokens if tokens is not None else self._count_tokens()
        self._index: int = Message.index
        Message.index += 1

    def to_dict_reduced_context(self) -> dict:
        """Use this lightweight version when sending messages to API endpoints.
        If we send less, we save tokens.

        Returns:
            dict: A lightweight dictionary representation of the Message class.
        """
        return {
            "role": self._role,
            "content": self._content,
        }

    def to_dict_full_context(self) -> dict:
        """Use this version when storing messages locally in your machine.
        When storing messages locally, we want the full context for each message.

        Returns:
            dict: A complete dictionary representation of the Message class.
        """
        return {
            "created": self._created,
            "uuid": self._uuid,
            "role": self._role,
            "content": self._content,
            "model": self._model,
            "is_reply": self._is_reply,
            "tokens": self._tokens,
            "index": self._index,
        }

    def _count_tokens(self) -> int:
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
            raise NotImplementedError(f"_count_tokens() is not presently implemented for {self._model}.")
        else:
            encoding: Encoding = self._encoding()
            num_tokens: int = 0
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += len(encoding.encode(self._content))
            if self._role == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
            if self._is_reply:
                num_tokens += 2  # every reply is primed with <im_start>assistant

            return num_tokens

    def _encoding(self) -> Encoding:
        """Determine the encoding to use for the Message.
        The encoding is derived from the LLM model used, via tiktoken.

        Returns:
            Encoding: The encoding of the message, which is the encoding used for the model.
        """
        try:
            return tiktoken.encoding_for_model(model_name=self._model)
        except KeyError:
            return tiktoken.get_encoding(encoding_name="cl100k_base")  # keep this here
            # sometimes updates to tiktoken are late for new models, therefore default to 'cl100k_base'

    @property
    def tokens(self) -> int:
        return self._tokens


class MessageFactory:
    """A factory for creating messages."""

    @staticmethod
    def create_user_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content.

        Args:
            role (str): The role designated by the user at the start (user, mathematician, pilot etc).
            content (str): The content of the message body.
            model (str): The LLM used for this message.

        Returns:
            Message: A Message object specially suited for user generated messages.
        """
        return Message(
            role=role,
            content=content,
            model=model,
            is_reply=False,
        )

    @staticmethod
    def create_reply_message(role: str, content: str, model: str) -> Message:
        """Creates a message, you may specify the role and the content.

        Args:
            role (str): The role designated by the user at the start (user, mathematician, pilot etc).
            content (str): The content of the message body.
            model (str): The LLM used for this message.

        Returns:
            Message: A Message object specially suited for user generated messages.
        """
        return Message(
            role=role,
            content=content,
            model=model,
            is_reply=True,
        )

    @staticmethod
    def create_message_from_dict(message: dict) -> Message:
        """Creates a message from a dictionary.
        See the Storage module as an example.

        Args:
            message (dict): A dictionary representation of a message.
            Must contain all the context as a locally stored Message would.

        Returns:
            Message: A Message object specially suited for user generated messages.
        """
        if not isinstance(message, dict):
            raise TypeError(f"Expected 'message' parameter to be of type 'dict' and not '{type(message)}'.")
        return Message(
            role=message["role"],
            content=message["content"],
            model=message["model"],
            is_reply=message["is_reply"],
            created=message["created"],
            uuid=message["uuid"],
            tokens=message["tokens"],
        )


class Messages:
    """A class to hold Message objects.

    It fulfills the need of custom functionalities
    that are not offered by Python dictionaries or lists.
    """

    def __init__(self, messages: list[Message] | None = None) -> None:
        self._uuid: str = str(uuid4())
        self._messages: Union[list[Message] | list] = messages if messages is not None else list()
        self._tokens: int = self._count_tokens()
        self._count: int = len(self._messages)

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
            self._count += 1

    def to_json(self, indent: Union[int, str, None] = None) -> str:
        """Convert all Message objects in Messages to JSON serialized object."""
        logger.info("Generating json from Messages.")
        return json.dumps(
            {
                "messages": [message.to_dict_full_context() for message in self._messages],
                "summary": {
                    "tokens": self._tokens,
                    "count": self._count,
                },
            },
            indent=indent,
            ensure_ascii=False,
        )

    def _count_tokens(self) -> int:
        logger.info("Counting total number of used in messages.")
        if len(self._messages) == 0:
            logger.warning("No Message objects found in Messages.")
            return 0
        else:
            count: int = 0
            for message in self._messages:
                count += message.tokens
            return count

    @property
    def tokens(self) -> int:
        return self._tokens

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return MessagesIterator(self._messages)


class MessagesIterator:
    """A simple Messages iterator to promote the usage of
    'message in messages' and not 'message in messages.messages'
    """

    def __init__(self, messages: list[Message]) -> None:
        self._index: int = 0
        self._messages: list[Message] = messages

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._messages):
            message = self._messages[self._index]
            self._index += 1
            return message
        else:
            raise StopIteration
