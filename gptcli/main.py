#!/usr/bin/env python3
"""The entrypoint to the project."""
import os
from gptcli.definitions import GPTCLI_KEYS_OPENAI, OPENAI_API_KEY
import logging

from gptcli.src.chat import ChatOpenai
from gptcli.src.cli import CommandParser
from gptcli.src.install import Install

logger = logging.getLogger(__name__)


def run_and_configure_argparse() -> CommandParser:
    logger.info("Running and configuring argparse.")
    parser: CommandParser = CommandParser()
    parser.configure_command_parser()
    return parser


def load_api_key_to_environment_variable() -> None:
    with open(GPTCLI_KEYS_OPENAI, "r", encoding="utf8") as filepointer:
        os.environ[OPENAI_API_KEY] = filepointer.read()


def execute_install(parser: CommandParser) -> None:
    logger.info("Executing install script.")
    Install(openai_api_key=parser.args.key).standard_install()


def enter_cli_mode(parser: CommandParser) -> None:
    logger.info("Entering CLI mode.")
    logger.warning("CLI mode is not currently implemented: %s", parser.args)
    raise NotImplementedError("CLI only mode not implemented yet.")


def enter_chat_mode(parser: CommandParser) -> None:
    logger.info("Entering chat mode.")
    ChatOpenai(
        model=parser.args.model,
        context=parser.args.context,
        stream=parser.args.stream,
        filepath=parser.args.filepath,
        storage=parser.args.storage,
        continue_chat=parser.args.continue_chat,
    ).start()


def main() -> None:
    """This is the main function."""
    parser: CommandParser = run_and_configure_argparse()
    if "key" not in parser.args or len(parser.args.key) == 0:
        load_api_key_to_environment_variable()
        parser.args.key = os.environ[OPENAI_API_KEY]
    execute_install(parser=parser)
    match parser.args.subcommand_name:
        case "se":
            enter_cli_mode(parser=parser)
        case "chat":
            enter_chat_mode(parser=parser)
        case _:
            print("[GPTCLI] Message: It seems you have not selected a mode. Try using 'gptcli -h/--help'.")


if __name__ == "__main__":
    main()
