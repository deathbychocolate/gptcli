"""Main command line interface."""

import argparse
import logging
from logging import Logger

from gptcli._version import __version__
from gptcli.src.supported_models import openai

logger: Logger = logging.getLogger(__name__)


def custom_formatter(prog):
    return argparse.RawTextHelpFormatter(prog, max_help_position=40)


epilog: str = """
Tips and Tricks:
    Yes, there are some tips and tricks:
    - You can use multiline input while in prompt mode by starting your message with \"\"\" + `ENTER` and ending it with \"\"\" + `ENTER`.
    - You can exit chat mode by typing and entering `exit` or `q` or `CRTL+C`.
    - You can abort any process via `CRTL+C`.
    - You can cycle through your sent messages in your active chat session via the arrow keys: `up` and `down`.
"""


class CommandLineInterface:
    """Class for the command line interface."""

    LOGGING_MODE_ALL = [
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
            epilog=epilog,
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
            choices=CommandLineInterface.LOGGING_MODE_ALL,
            default=logging.CRITICAL,
            help=f"Defaults to {logging.CRITICAL}. Set the log level of the application.",
        )
        self.parser.add_argument(
            "--mode",
            type=str,
            choices=["cli", "chat"],
            default="chat",
            help="Defaults to 'chat'. The mode to run 'gptcli' in.",
        )
        self.parser.add_argument(
            "--model",
            type=str,
            choices=openai.values(),
            default=openai["GPT_4O"],
            help=f"Defaults to '{openai['GPT_4O']}'. The model to use.",
        )
        self.parser.add_argument(
            "--key",
            type=str,
            default="",
            help="Defaults to the key stored in .gptcli in your home dir. The API key to use for the run.",
            metavar="<string>",
        )
        self.parser.add_argument(
            "--role-user",
            type=str,
            default="user",
            help="Defaults to 'user'. The user may assume a role other than 'user'.",
            metavar="<string>",
        )
        self.parser.add_argument(
            "--role-model",
            type=str,
            default="assistant",
            help="Defaults to 'assistant'. The language model may assume a role other than 'assistant'.",
            metavar="<string>",
        )
        self.parser.add_argument(
            "--filepath",
            type=str,
            default="",
            help="Select a file with text to ingest and use for context.",
            metavar="<string>",
        )
        self.parser.add_argument(
            "--context",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable the sending of past messages from the same chat session. Use to conserve tokens.",
        )
        self.parser.add_argument(
            "--stream",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable streaming mode.",
        )
        self.parser.add_argument(
            "--storage",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Enable or disable local storage of last chat session.",
        )
        self.parser.add_argument(
            "--continue-chat",
            action=argparse.BooleanOptionalAction,
            default=False,
            help="Enable or disable loading your last chat session from storage.",
        )

        self.args = self.parser.parse_args()

    def configure_cli(self) -> None:
        """Used to run any final configurations we want regarding the argparse parameters."""
        logger.info("Running cli")
        self._configure_logging_level()

    def _configure_logging_level(self) -> None:
        logger.info("Configuring logging level")
        log_level = self.args.loglevel
        logging.basicConfig(level=log_level)
