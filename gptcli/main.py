#!/usr/bin/env python3
"""This is the main file for the project"""
import logging

from gptcli.src.chat import ChatOpenai
from gptcli.src.cli import CommandLineInterface
from gptcli.src.install import Install

logger = logging.getLogger(__name__)


def main() -> None:
    """This is the main function"""
    cli = CommandLineInterface()
    cli.run()

    Install(openai_api_key=cli.args.key).standard_install()

    ChatOpenai(
        model=cli.args.model,
        context=cli.args.context,
        stream=cli.args.stream,
        filepath=cli.args.filepath,
    ).start()


if __name__ == "__main__":
    main()
