#!/usr/bin/env python3
"""The entrypoint to the project."""
import logging

from gptcli.src.chat import ChatOpenai
from gptcli.src.cli import CommandLineInterface
from gptcli.src.install import Install

logger = logging.getLogger(__name__)


def run_and_configure_argparse() -> CommandLineInterface:
    logger.info("Running and configuring argparse.")
    cli: CommandLineInterface = CommandLineInterface()
    cli.configure_cli()
    return cli


def execute_install(cli: CommandLineInterface) -> None:
    logger.info("Executing install script.")
    Install(openai_api_key=cli.args.key).standard_install()


def enter_cli_mode(cli: CommandLineInterface) -> None:
    logger.info("Entering CLI mode.")
    logger.warning("CLI mode is not currently implemented: %s", cli.args)
    raise NotImplementedError("CLI only mode not implemented yet.")


def enter_chat_mode(cli: CommandLineInterface) -> None:
    logger.info("Entering chat mode.")
    ChatOpenai(
        model=cli.args.model,
        context=cli.args.context,
        stream=cli.args.stream,
        filepath=cli.args.filepath,
        storage=cli.args.storage,
        continue_chat=cli.args.continue_chat,
    ).start()


def main() -> None:
    """This is the main function."""
    cli: CommandLineInterface = run_and_configure_argparse()
    execute_install(cli=cli)
    match cli.args.mode:
        case "cli":
            enter_cli_mode(cli=cli)
        case "chat":
            enter_chat_mode(cli=cli)
        case _:
            logger.error("Mode '%s' not recognized.", cli.args.mode)


if __name__ == "__main__":
    main()
