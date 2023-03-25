"""
Main command line interface.
"""

import readline
import logging
import argparse

from src.main.openai_helper import OpenAIHelper

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
            help="Will print the version of the application",
        )
        self.parser.add_argument(
            "-l",
            "--loglevel",
            type=int,
            choices=CommandLineInterface.LOGGING_MODE_ALL,
            default=logging.CRITICAL,
            help="Will set the log level of the application. Defaults to CRITICAL.",
        )
        self.parser.add_argument(
            "-m",
            "--model",
            type=str,
            choices=OpenAIHelper.GPT_ALL,
            default=OpenAIHelper.GPT_DEFAULT,
            help=f"The model to use. Defaults to {OpenAIHelper.GPT_DEFAULT}",
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
        Will start the gptcli
        """
        logger.info("Running cli")
        self._configure_logging()
        self._configure_readline()
        self._start_chat()

    def _configure_logging(self) -> None:
        """
        Will set the logging level
        """
        log_level = self.args.loglevel
        if log_level != 50:
            logging.basicConfig(level=log_level)
        else:
            logging.basicConfig(level=logging.CRITICAL)
        logging.info("Logging level set to %s", log_level)

    def _configure_readline(self) -> None:
        readline.parse_and_bind("'^[[A': history-search-backward")
        readline.parse_and_bind("'^[[B': history-search-forward")
        readline.parse_and_bind("'^[[C': forward-char")
        readline.parse_and_bind("'^[[D': backward-char")

    def _start_chat(self) -> None:
        logger.info("Starting chat")
        while True:

            # check for KeyboardInterrupt and EOFError
            try:
                user_input = input(">>> USER: ")
            except KeyboardInterrupt as exception:
                logger.info("Keyboard interrupt detected")
                logger.exception(exception)
                break
            except EOFError as exception:
                logger.info("EOF detected")
                logger.exception(exception)
                break

            # check for special commands
            user_input_length = len(user_input)
            if user_input_length == 0:
                continue
            elif user_input == "exit":
                break

            model = self.args.model.lower()
            response = OpenAIHelper(model, user_input).send()
            print("".join([">>> AI: ", response]))
