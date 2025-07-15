"""The entrypoint to the project."""

import logging
import os
from logging import Logger

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    MISTRAL_API_KEY,
    OPENAI_API_KEY,
)
from gptcli.src.cli import CommandParser
from gptcli.src.common.constants import ProviderNames
from gptcli.src.install import Mistral, Openai
from gptcli.src.modes.chat import ChatUser
from gptcli.src.modes.single_exchange import SingleExchange

logger: Logger = logging.getLogger(__name__)


def run_and_configure_argparse() -> CommandParser:
    logger.info("Running and configuring argparse.")
    parser: CommandParser = CommandParser()
    parser.configure_command_parser()
    return parser


def load_api_key_to_environment_variable(parser: CommandParser) -> None:
    logger.info("Exporting API key to environment variables.")

    # Make sure the values assigned correspond to the correct provider.
    if parser.args.provider == ProviderNames.MISTRAL.value:
        file = GPTCLI_PROVIDER_MISTRAL_KEY_FILE
        key_name = MISTRAL_API_KEY
    elif parser.args.provider == ProviderNames.OPENAI.value:
        file = GPTCLI_PROVIDER_OPENAI_KEY_FILE
        key_name = OPENAI_API_KEY
    else:
        raise NotImplementedError(f"Provider '{parser.args.provider}' not yet supported.")

    if "key" in parser.args and parser.args.key is None:
        try:
            with open(file, "r", encoding="utf8") as fp:
                os.environ[key_name] = fp.read()
        except FileNotFoundError:
            logger.warning("File storing API key not found. Skipping loading API from local storage.")
    elif "key" in parser.args and str(parser.args.key).isascii():
        os.environ[key_name] = str(parser.args.key)


def enter_single_exchange_mode(parser: CommandParser) -> None:
    logger.info("Entering CLI mode.")
    SingleExchange(
        input_string=parser.args.input_string,
        model=parser.args.model,
        provider=parser.args.provider,
        role_user=parser.args.role_user,
        role_model=parser.args.role_model,
        filepath=parser.args.filepath,
        output=parser.args.output,
    ).start()


def enter_chat_mode(parser: CommandParser) -> None:
    logger.info("Entering chat mode.")
    ChatUser(
        model=parser.args.model,
        provider=parser.args.provider,
        role_user=parser.args.role_user,
        role_model=parser.args.role_model,
        context=parser.args.context,
        stream=parser.args.stream,
        filepath=parser.args.filepath,
        store=parser.args.store,
        load_last=parser.args.load_last,
    ).start()


def main() -> None:
    """This is the main function."""
    parser: CommandParser = run_and_configure_argparse()

    # print help when ...
    if not parser.args.provider:  # provider is missing
        parser.print_help()
        return None
    elif not parser.args.mode_name:  # mode is missing
        parser.print_help_provider(provider=parser.args.provider)
        return None

    # install
    match parser.args.provider:
        case ProviderNames.MISTRAL.value:
            Mistral().install()
        case ProviderNames.OPENAI.value:
            Openai().install()
        case _:
            raise NotImplementedError(f"Provider '{parser.args.provider}' not yet supported.")

    load_api_key_to_environment_variable(parser=parser)

    match parser.args.mode_name:
        case "se":
            enter_single_exchange_mode(parser=parser)
            return None
        case "chat":
            enter_chat_mode(parser=parser)
            return None

    return None


if __name__ == "__main__":
    main()
