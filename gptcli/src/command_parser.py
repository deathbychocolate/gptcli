"""This file holds GPTCLI's implementation of argparse and other related configurations (ie logging)"""

import argparse
import logging
from logging import Logger
from typing import ClassVar

from gptcli._version import __version__
from gptcli.src.definitions import openai, output_types, roles

logger: Logger = logging.getLogger(__name__)


def custom_formatter(prog):
    return argparse.RawTextHelpFormatter(prog, max_help_position=40)


epilog_chat: str = """
Tips and Tricks:
    Yes, there are some tips and tricks:
    - You can use multiline input while in prompt mode by starting your message with \"\"\" + `ENTER` and ending it with \"\"\" + `ENTER`.
    - You can exit chat mode by typing and entering `exit` or `q`.
    - You can clear your terminal's screen by typing and entering `clear` or `cls`.
    - You can abort any process via `CTRL+C`.
    - You can cycle through your sent messages in your active chat session via the arrow keys: `up` and `down`.
"""


class CommandParser:
    """Class for the command line interface."""

    LOGGING_MODE_ALL: ClassVar[list[int]] = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]

    def __init__(self) -> None:
        # pylint: disable=line-too-long
        self.parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=custom_formatter,
        )
        self.parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=__version__,
            help="Print the version number and exit.",
        )
        self.parser.add_argument(
            "--loglevel",
            type=int,
            choices=CommandParser.LOGGING_MODE_ALL,
            default=logging.CRITICAL,
            help=f"Defaults to {logging.CRITICAL}. Set the log level of the application.",
        )

        # create the top-level parser
        subparsers = self.parser.add_subparsers(
            help="The 2 modes available to GPTCLI.",
            dest="subcommand_name",
        )

        # parser options for 'single-exchange' mode
        parser_se = subparsers.add_parser(
            "se",
            formatter_class=custom_formatter,
            help="'Single-Exchange' mode is a mode optimized for 1 message-reply transaction.",
        )
        parser_se.add_argument(
            "--model",
            type=str,
            choices=openai.values(),
            default=openai["GPT_4O"],
            help=f"Defaults to '{openai['GPT_4O']}'. The model to use.",
        )
        parser_se.add_argument(
            "--key",
            type=str,
            help="Defaults to the key stored in .gptcli in your home dir. The API key to use for the run.",
            metavar="<string>",
        )
        parser_se.add_argument(
            "--role-user",
            type=str,
            default="user",
            choices=roles,
            help="Defaults to 'user'. The user may assume a role other than 'user'.",
            metavar="<string>",
        )
        parser_se.add_argument(
            "--role-model",
            type=str,
            default="assistant",
            choices=roles,
            help="Defaults to 'assistant'. The language model may assume a role other than 'assistant'.",
            metavar="<string>",
        )
        parser_se.add_argument(
            "--filepath",
            type=str,
            default="",
            help="Select a file with text to ingest and use for context.",
            metavar="<string>",
        )
        parser_se.add_argument(
            "--storage",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable local storage of last chat session.",
        )
        parser_se.add_argument(
            "--output",
            type=str,
            choices=output_types.values(),
            default=output_types["plain"],
            help="Defaults to 'plain'. The output format of the reply message.",
        )
        parser_se.add_argument(
            "input_string",
            type=str,
            help="Accepts a string input of any size.",
        )

        # parser options for 'chat' mode
        parser_chat = subparsers.add_parser(
            "chat",
            formatter_class=custom_formatter,
            help="'Chat' mode is optimized for having multiple (>1) message-reply transactions.",
            epilog=epilog_chat,
        )
        parser_chat.add_argument(
            "--model",
            type=str,
            choices=openai.values(),
            default=openai["GPT_4O"],
            help=f"Defaults to '{openai['GPT_4O']}'. The model to use.",
        )
        parser_chat.add_argument(
            "--key",
            type=str,
            help="Defaults to the key stored in .gptcli in your home dir. The API key to use for the run.",
            metavar="<string>",
        )
        parser_chat.add_argument(
            "--role-user",
            type=str,
            default="user",
            help="Defaults to 'user'. The user may assume a role other than 'user'.",
            metavar="<string>",
        )
        parser_chat.add_argument(
            "--role-model",
            type=str,
            default="assistant",
            help="Defaults to 'assistant'. The language model may assume a role other than 'assistant'.",
            metavar="<string>",
        )
        parser_chat.add_argument(
            "--filepath",
            type=str,
            default="",
            help="Select a file with text to ingest and use for context.",
            metavar="<string>",
        )
        parser_chat.add_argument(
            "--context",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable the sending of past messages from the same chat session. Use to conserve tokens.",
        )
        parser_chat.add_argument(
            "--stream",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable streaming mode.",
        )
        parser_chat.add_argument(
            "--storage",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable local storage of last chat session.",
        )
        parser_chat.add_argument(
            "--load-last",
            action=argparse.BooleanOptionalAction,
            default=False,
            help="Enable or disable loading your last chat session from storage.",
        )

        self.args = self.parser.parse_args()

    def configure_command_parser(self) -> None:
        """Used to run any final configurations we want regarding the argparse parameters."""
        logger.info("Running cli")
        self._configure_logging_level()

    def _configure_logging_level(self) -> None:
        logger.info("Configuring logging level")
        log_level = self.args.loglevel
        logging.basicConfig(level=log_level)
