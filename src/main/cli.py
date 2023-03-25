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
            choices=["debug", "info", "warning", "error", "critical"],
            default="critical",
            help="Will set the log level of the application. Defaults to INFO.",
        )
        self.parser.add_argument(
            "-m",
            "--model",
            choices=["gpt-3.5-turbo", "gpt-3.5-turbo-0301", "gpt-4-0314"],
            default="gpt-3.5-turbo-0301",
            help="The model to use. Defaults to gpt-3.5() gpt-4-0314.",
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
        logger.info("Starting gptcli")
        self._set_logging_level()
        readline.parse_and_bind('"^[[A": history-search-backward')
        readline.parse_and_bind('"^[[B": history-search-forward')
        readline.parse_and_bind('"^[[C": forward-char')
        readline.parse_and_bind('"^[[D": backward-char')
        while True:
            try:
                user_input = input(">>> USER: ")
            except KeyboardInterrupt as exception:
                break
            except EOFError as exception:
                break
            user_input_length = len(user_input)
            if user_input_length == 0:
                continue
            elif user_input == "exit":
                break
            response = OpenAIHelper(OpenAIHelper.ENGINE_GPT_3_5_301, user_input).send()
            print("".join([">>> AI: ", response]))

    # def _clean_input(self, user_input: str) -> str:
    #     """
    #     Will clean the input from the user
    #     """
    #     return user_input.strip()
    def _set_logging_level(self) -> None:
        """
        Will set the logging level
        """
        log_level = self.args.loglevel.upper()
        if log_level != "CRITICAL":
            logging.basicConfig(level=log_level)
        else:
            logging.basicConfig(level=logging.CRITICAL)
        logging.info("Logging level set to %s", log_level)
