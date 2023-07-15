"""Main command line interface.
"""

import argparse
import logging

from gptcli._version import __version__
from gptcli.src.api_helper import OpenAIHelper

logger = logging.getLogger(__name__)


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
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=__version__,
            help="Print the version number and exit.",
        )
        self.parser.add_argument(
            "-l",
            "--loglevel",
            type=int,
            choices=CommandLineInterface.LOGGING_MODE_ALL,
            default=logging.CRITICAL,
            help="Set the log level of the application. Defaults to CRITICAL.",
        )
        self.parser.add_argument(
            "-m",
            "--model",
            type=str,
            choices=OpenAIHelper.GPT_ALL,
            default=OpenAIHelper.GPT_DEFAULT,
            help=f"The model to use. Defaults to {OpenAIHelper.GPT_DEFAULT}.",
        )
        self.parser.add_argument(
            "-k",
            "--key",
            type=str,
            default="",
            help="The API key to use for the run. Defaults to the key stored in .gptcli in your home dir.",
        )
        self.parser.add_argument(
            "-ru",
            "--role-user",
            type=str,
            default="user",
            help="Defaults to 'user'. Allows the user to assume a role other than 'user'.",
        )
        self.parser.add_argument(
            "-rm",
            "--role-model",
            type=str,
            default="assistant",
            help="Defaults to 'assistant'. Allows the LLM to assume a role other than 'assistant'.",
        )
        self.parser.add_argument(
            "-c",
            "--context",
            type=str,
            choices=["on", "off"],
            default="on",
            help="Defaults to 'on'. Enable or disable sending all chat messages to API to build a better reply. Use 'off' to conserve tokens.",
        )
        self.parser.add_argument(
            "-s",
            "--stream",
            type=str,
            choices=["on", "off"],
            default="on",
            help="Defaults to 'on'. Enables streaming mode for text replies in chat mode.",
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
