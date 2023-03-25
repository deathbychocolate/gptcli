"""
Main command line interface.
"""

import logging
import argparse

from src.main.openai_helper import OpenAIHelper

logging.basicConfig(level=logging.INFO)
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
            help="log level",
        )
        self.parser.add_argument(
            "-m",
            "--model",
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
        logger.info("Rendering gptcli")
        while True:
            user_input = input(">>> USER: ")
            if user_input == "exit":
                break
            response = OpenAIHelper(OpenAIHelper.ENGINE_GPT_3_5_301, user_input).send()
            print("".join([">>> AI: ", response]))
    
    # def _clean_input(self, user_input: str) -> str:
    #     """
    #     Will clean the input from the user
    #     """
    #     return user_input.strip()
