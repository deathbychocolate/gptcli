"""
Main command line interface.
"""

import logging
import argparse

from src.main.openai_helper import OpenAIHelper
from src.main.chat import Chat

logger = logging.getLogger(__name__)


class CommandLineInterface:
    """
    Class for the command line interface.
    """

    LOGGING_MODE_ALL = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version="0.0.0",
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
        # self.parser.add_argument(
        #     "-c",
        #     "--context",
        #     help="The context to use. Defaults to off (no context) for saving tokens.",
        # )
        # self.parser.add_argument(
        #     "configure",
        #     help="Configure the application",
        # )

        self.args = None

    def parse(self) -> None:
        """
        Will parse the arguments and store them in self.args
        """
        self.args = self.parser.parse_args()

    def run(self) -> None:
        """
        Run this method if you want to start a classic dialog with the AI
        """
        logger.info("Running cli")
        self._configure_logging_level()
        self._start_chat_session()

    def _configure_logging_level(self) -> None:
        logger.info("Configuring logging level")
        log_level = self.args.loglevel
        logging.basicConfig(level=log_level)

    def _start_chat_session(self) -> None:
        logger.info("Starting chat session")
        chat_session = self._create_chat_session()
        chat_session.start()

    def _create_chat_session(self) -> Chat:
        logger.info("Creating chat session")
        return Chat(self.args.model)
