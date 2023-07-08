#!/usr/bin/env python3
"""
This is the main file for the project
"""
import logging

from gptcli.src.chat import ChatOpenai
from gptcli.src.cli import CommandLineInterface
from gptcli.src.install import Install

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
        model=cli.args.model,
        context=cli.args.context,
        stream=cli.args.stream,
    )
    chat.start()


if __name__ == "__main__":
    main()
