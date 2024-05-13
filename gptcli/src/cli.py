"""Main command line interface.
"""

import argparse
import logging
from logging import Logger

from gptcli._version import __version__
from gptcli.src.supported_models import openai

logger: Logger = logging.getLogger(__name__)


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
        self.parser = argparse.ArgumentParser(add_help=False)
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
            "--model",
            type=str,
            choices=openai.values(),
            default=openai["GPT_4O"],
            help=f"Defaults to {openai['GPT_4O']}. The model to use.",
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
            "--context",
            type=str,
            choices=["on", "off"],
            default="on",
            help="Defaults to 'on'. Send all chat messages to API to build a better reply. Use 'off' to conserve tokens.",
        )
        self.parser.add_argument(
            "--stream",
            type=str,
            choices=["on", "off"],
            default="on",
            help="Defaults to 'on'. Streaming mode for text replies in chat mode.",
        )
        self.parser.add_argument(
            "--filepath",
            type=str,
            default="",
            help="Select a file with text to ingest and use for context.",
            metavar="<string>",
        )

        self.args = self.parser.parse_args()

    def run(self) -> None:
        """Run this method if you want to start a classic dialog with the AI"""
        logger.info("Running cli")
        self._configure_logging_level()

    def _configure_logging_level(self) -> None:
        logger.info("Configuring logging level")
        log_level = self.args.loglevel
        logging.basicConfig(level=log_level)
