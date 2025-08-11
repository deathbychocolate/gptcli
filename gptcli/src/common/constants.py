"""Contains commonly used strings for interacting with an AI Provider."""

from enum import Enum
from textwrap import dedent


class BaseEnum(Enum):
    """The base class meant to hold all common methods and functions
    for classes in the 'constants' module.
    """

    @classmethod
    def to_list(cls) -> list[str]:
        """Get the class variable values in list[str] form."""
        return [class_var.value for class_var in cls]


class ChatColours(BaseEnum):
    """The colours to use for CLI output."""

    GRY = "\033[38;5;245m"  # darker ANSI grey - for placeholder
    GRN = "\033[1;38;5;2m"  # bold green - for user
    MGA = "\033[1;38;5;13m"  # bold magenta - for AI
    RST = "\033[0m"  # reset the colour to default

    @classmethod
    def grey(cls) -> str:
        """Return the colour code for darker ANSI grey."""
        return cls.GRY.value

    @classmethod
    def green(cls) -> str:
        """Return the colour code for bold green."""
        return cls.GRN.value

    @classmethod
    def magenta(cls) -> str:
        """Return the colour code for bold magenta."""
        return cls.MGA.value

    @classmethod
    def reset(cls) -> str:
        """Return the colour code reset."""
        return cls.RST.value


# Useful shorthand:
GRY: str = ChatColours.GRY.value
GRN: str = ChatColours.GRN.value
MGA: str = ChatColours.MGA.value
RST: str = ChatColours.RST.value


class ChatCommands(BaseEnum):
    """The chat commands to use when in Chat mode."""

    # Multiline.
    M = "/m"
    MULT = "/mult"

    # Exit/Quit.
    Q = "/q"
    QUIT = "/quit"
    E = "/e"
    EXIT = "/exit"

    # Clear.
    CLEAR = "/c"
    CLEAR_UNIX = "/clear"
    CLEAR_WINDOWS = "/cls"

    # Help.
    QUESTION_MARK = "/?"
    H = "/h"
    HELP = "/help"

    @classmethod
    def multiline(cls) -> list[str]:
        """Returns a list of all commands that enable multiline mode."""
        return [cls.M.value, cls.MULT.value]

    @classmethod
    def exit(cls) -> list[str]:
        """Returns a list of all exit commands."""
        return [cls.Q.value, cls.QUIT.value, cls.E.value, cls.EXIT.value]

    @classmethod
    def clear(cls) -> list[str]:
        """Returns a list of clear screen commands."""
        return [cls.CLEAR.value, cls.CLEAR_WINDOWS.value, cls.CLEAR_UNIX.value]

    @classmethod
    def help(cls) -> list[str]:
        """Returns as list of help commands."""
        return [cls.QUESTION_MARK.value, cls.H.value, cls.HELP.value]

    @staticmethod
    def help_doc() -> str:
        """Return a dedented help doc."""
        return dedent(
            """
            /?, /h, /help           Show help.
            /c, /cls, /clear        Clear screen.
            /m, /mult               Enter multiline mode.
            /e, /exit, /q, /quit    End program.
            ↑/↓                     Navigate history.
            Enter                   Send message.
            """
        )


MULT: str = ChatCommands.MULT.value


class ProviderNames(BaseEnum):
    """The provider names currently supported. No default value needed."""

    MISTRAL = "mistral"
    OPENAI = "openai"

    @classmethod
    def mistral(cls) -> str:
        """Return the mistral value."""
        return cls.MISTRAL.value

    @classmethod
    def openai(cls) -> str:
        """Return the openai value."""
        return cls.OPENAI.value


# Useful shorthand:
MISTRAL: str = ProviderNames.MISTRAL.value
OPENAI: str = ProviderNames.OPENAI.value


class UserRoles(BaseEnum):
    """Contains user roles that are common across all models.
    Passed to Message objects to instruct the AI model how to behave.
    """

    USER = "user"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.USER.value


class ModelRoles(BaseEnum):
    """Contains model roles that are common across all models.
    Passed to Message objects to instruct the AI model how to behave.
    """

    ASSISTANT = "assistant"
    FUNCTION = "function"
    SYSTEM = "system"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.ASSISTANT.value


class OpenaiUserRoles(BaseEnum):
    """The roles assigned to messages from the client side.

    See here for more details: https://model-spec.openai.com/2025-02-12.html#chain_of_command
    """

    PLATFORM = "platform"  # level 1 (highest) (strict)
    DEVELOPER = "developer"  # level 2 (strict)
    GUIDELINE = "guideline"  # level 3 (permissive)
    USER = "user"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.USER.value


class OpenaiModelRoles(BaseEnum):
    """Passed to Message objects to instruct the AI model how to behave."""

    ASSISTANT = "assistant"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.ASSISTANT.value


class OpenaiModelsChat(BaseEnum):
    """The models that can be used in chat mode without issue.

    See here for more details: https://platform.openai.com/docs/models/
    """

    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    O1 = "o1"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O4_MINI = "o4-mini"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.GPT_5_MINI.value


class MistralUserRoles(BaseEnum):
    """Passed to Message objects to instruct the AI model how to behave."""

    USER = "user"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.USER.value


class MistralModelRoles(BaseEnum):
    """Passed to Message objects to instruct the AI model how to behave."""

    ASSISTANT = "assistant"
    FUNCTION = "function"
    SYSTEM = "system"
    TOOL = "tool"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.ASSISTANT.value


class MistralModelsChat(BaseEnum):
    """The models that can be used in chat mode without issue.

    See here for more details:
    https://docs.mistral.ai/getting-started/models/models_overview/
    https://github.com/mistralai/mistral-common/blob/main/docs/models.md

    Note that Chat models by Mistral in the `models.md` file are marked
    as `Generation` under the 'Task' column, and ✅ under the 'Text'
    column.

    Note that models available to an API key may not yet be available in
    the `mistral-common` package.

    To view the chat models available to an API key, run the following
    in your terminal:
    `curl -s https://api.mistral.ai/v1/models \
        -H "Authorization: Bearer $MISTRAL_API_KEY" \
        -H "Content-Type: application/json"`
    """

    MISTRAL_TINY = "mistral-tiny-2407"
    MISTRAL_SMALL = "mistral-small-2409"
    MISTRAL_MEDIUM = "mistral-medium-2312"
    MISTRAL_LARGE = "mistral-large-2411"
    MISTRAL_NEMO = "open-mistral-nemo-2407"
    PIXTRAL_12B = "pixtral-12b-2409"
    PIXTRAL_LARGE = "pixtral-large-2411"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.MISTRAL_LARGE.value


class OutputTypes(BaseEnum):
    """Used exclusively with the single-exchange option to determine how to print the output."""

    ALL = "all"
    CHOICES = "choices"
    PLAIN = "plain"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.PLAIN.value


class StorageTypes(BaseEnum):
    """The storage types the project supports."""

    DB = "db"
    JSON = "json"

    @classmethod
    def default(cls) -> str:
        """Returns the default value."""
        return cls.DB.value
