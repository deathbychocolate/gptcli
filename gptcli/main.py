#!/usr/bin/env python3
"""The entrypoint to the project."""
import logging
import os
from logging import Logger

from gptcli.definitions import GPTCLI_KEYS_OPENAI, OPENAI_API_KEY
from gptcli.src.chat import ChatOpenai
from gptcli.src.command_parser import CommandParser
from gptcli.src.install import Install
from gptcli.src.single_exchange import SingleExchange

logger: Logger = logging.getLogger(__name__)


def run_and_configure_argparse() -> CommandParser:
    logger.info("Running and configuring argparse.")
    parser: CommandParser = CommandParser()
    parser.configure_command_parser()
    return parser


def load_api_key_to_environment_variable(parser: CommandParser) -> None:
    if "key" in parser.args and parser.args.key is None:
        try:
            with open(GPTCLI_KEYS_OPENAI, "r", encoding="utf8") as filepointer:
                os.environ[OPENAI_API_KEY] = filepointer.read()
        except FileNotFoundError:
            logger.warning("File storing API key not found. Skipping loading API from local storage.")
    elif "key" in parser.args and str(parser.args.key).isascii():
        os.environ[OPENAI_API_KEY] = str(parser.args.key)


def enter_single_exchange_mode(parser: CommandParser) -> None:
    logger.info("Entering CLI mode.")
    SingleExchange(
        input_string=parser.args.input_string,
        model=parser.args.model,
        role_user=parser.args.role_user,
        role_model=parser.args.role_model,
        filepath=parser.args.filepath,
        storage=parser.args.storage,
        output=parser.args.output,
    ).start()


def enter_chat_mode(parser: CommandParser) -> None:
    logger.info("Entering chat mode.")
    ChatOpenai(
        model=parser.args.model,
        role_user=parser.args.role_user,
        role_model=parser.args.role_model,
        context=parser.args.context,
        stream=parser.args.stream,
        filepath=parser.args.filepath,
        storage=parser.args.storage,
        load_last=parser.args.load_last,
    ).start()


def main() -> None:
    """This is the main function."""
    parser: CommandParser = run_and_configure_argparse()
    load_api_key_to_environment_variable(parser=parser)
    Install().standard_install()
    match parser.args.subcommand_name:
        case "se":
            enter_single_exchange_mode(parser=parser)
        case "chat":
            enter_chat_mode(parser=parser)
        case _:
            print("[GPTCLI] Message: It seems you have not selected a mode. Try using 'gptcli -h/--help'.")


if __name__ == "__main__":
    main()
