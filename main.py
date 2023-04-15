#!/usr/bin/env python3
"""
This is the main file for the project
"""
import logging

from src.main.cli import CommandLineInterface
from src.main.install import Install
from src.main.chat import ChatOpenai

logger = logging.getLogger(__name__)


def main() -> None:
    """
    This is the main function
    """
    cli = CommandLineInterface()
    cli.run()

    install = Install(openai_api_key=cli.args.key)
    install.standard_install()

    chat = ChatOpenai(
        cli.args.model,
        stream=cli.args.stream,
    )
    chat.start()


if __name__ == "__main__":
    main()
