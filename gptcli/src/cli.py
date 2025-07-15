"""This file holds GPTCLI's implementation of argparse and other related configurations (ie logging)."""

import argparse
import logging
from argparse import RawTextHelpFormatter
from logging import Logger
from typing import Any, ClassVar

from gptcli._version import __version__
from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
)
from gptcli.src.common.constants import (
    MistralModelRoles,
    MistralModelsChat,
    MistralUserRoles,
    OpenaiModelRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    OutputTypes,
    ProviderNames,
)

logger: Logger = logging.getLogger(__name__)


def custom_formatter(prog: Any) -> RawTextHelpFormatter:
    return argparse.RawTextHelpFormatter(prog, max_help_position=40)


def add_common_mode_arguments(subparser_modes: Any, provider: str) -> Any:
    """Add CLI arguments/flags that each provider is expected to have.

    Each provider is expected to at least have the following modes and
    corresponding flags: Chat, SingleExchange.

    Args:
        subparser_modes (SubParsersAction): The `openai` portion of the `gptcli openai chat`.
        provider (str): The provider the subparser is assigned to.

    Returns:
        SubParsersAction: The subparser with all modes and mode flags added.
    """

    all_models: list[str] = []
    default_key: str = ""
    default_model: str = ""
    default_role_user: str = ""
    default_role_model: str = ""
    default_role_user_choices: list[str] = []
    default_role_model_choices: list[str] = []
    if provider == ProviderNames.MISTRAL.value:
        all_models = MistralModelsChat.to_list()
        default_key = GPTCLI_PROVIDER_MISTRAL_KEY_FILE
        default_model = MistralModelsChat.default()
        default_role_user = MistralUserRoles.default()
        default_role_model = MistralModelRoles.default()
        default_role_user_choices = MistralUserRoles.to_list()
        default_role_model_choices = MistralModelRoles.to_list()
    elif provider == ProviderNames.OPENAI.value:
        all_models = OpenaiModelsChat.to_list()
        default_key = GPTCLI_PROVIDER_OPENAI_KEY_FILE
        default_model = OpenaiModelsChat.default()
        default_role_user = OpenaiUserRoles.default()
        default_role_model = OpenaiModelRoles.default()
        default_role_user_choices = OpenaiUserRoles.to_list()
        default_role_model_choices = OpenaiModelRoles.to_list()

    # parser options for 'single-exchange' mode
    parser_se = subparser_modes.add_parser(
        "se",
        formatter_class=custom_formatter,
        help="'Single-Exchange' mode is optimized for 1 message-reply transaction.",
    )
    parser_se.add_argument(
        "--model",
        type=str,
        choices=all_models,
        default=default_model,
        help=f"Defaults to '{default_model}'. The model to use.",
    )
    parser_se.add_argument(
        "--key",
        type=str,
        help=f"Defaults to the value in '{default_key}'. The API key to use for the run.",
        metavar="<string>",
    )
    parser_se.add_argument(
        "--role-user",
        type=str,
        default=default_role_user,
        choices=default_role_user_choices,
        help=f"Defaults to '{default_role_user}'. The user's chosen role during and exchange.",
    )
    parser_se.add_argument(
        "--role-model",
        type=str,
        default=default_role_model,
        choices=default_role_model_choices,
        help=f"Defaults to '{default_role_model}'. The model's chosen role during and exchange.",
    )
    parser_se.add_argument(
        "--filepath",
        type=str,
        default="",
        help="Select a file with text to ingest and use for context.",
        metavar="<string>",
    )
    parser_se.add_argument(
        "--output",
        type=str,
        default=OutputTypes.default(),
        choices=OutputTypes.to_list(),
        help="Defaults to 'plain'. The output format of the reply message.",
    )
    parser_se.add_argument(
        "input_string",
        type=str,
        help="Accepts a string input of any size.",
    )

    # parser options for 'chat' mode
    parser_chat = subparser_modes.add_parser(
        "chat",
        formatter_class=custom_formatter,
        help="'Chat' mode is optimized for multiple (>1) message-reply transactions.",
    )
    parser_chat.add_argument(
        "--model",
        type=str,
        choices=all_models,
        default=default_model,
        help=f"Defaults to '{default_model}'. The model to use.",
    )
    parser_chat.add_argument(
        "--key",
        type=str,
        help=f"Defaults to the value in '{default_key}'. The API key to use for the run.",
        metavar="<string>",
    )
    parser_chat.add_argument(
        "--role-user",
        type=str,
        default=default_role_user,
        choices=default_role_user_choices,
        help=f"Defaults to '{default_role_user}'. The user's chosen role during and exchange.",
        metavar="<string>",
    )
    parser_chat.add_argument(
        "--role-model",
        type=str,
        default=default_role_model,
        choices=default_role_model_choices,
        help=f"Defaults to '{default_role_model}'. The model's chosen role during and exchange.",
        metavar="<string>",
    )
    parser_chat.add_argument(
        "--filepath",
        type=str,
        default="",
        help="Select a file with text to ingest and use for context.",
        metavar="<string>",
    )
    parser_chat.add_argument(
        "--context",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable the sending of past messages from the same chat session. Use to conserve tokens.",
    )
    parser_chat.add_argument(
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable streaming mode.",
    )
    parser_chat.add_argument(
        "--store",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable local storage of last chat session.",
    )
    parser_chat.add_argument(
        "--load-last",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable or disable loading your last chat session from storage.",
    )

    return subparser_modes


class CommandParser:
    """Class for the command line interface."""

    LOGGING_MODE_ALL: ClassVar[list[int]] = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=custom_formatter,
        )
        self.parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )
        self.parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=__version__,
            help="Print the version number and exit.",
        )
        self.parser.add_argument(
            "--loglevel",
            type=int,
            choices=CommandParser.LOGGING_MODE_ALL,
            default=logging.CRITICAL,
            help=f"Defaults to {logging.CRITICAL}. Set the log level of the application.",
        )

        # create the top-level parser
        subparsers = self.parser.add_subparsers(
            help="The providers available.",
            dest="provider",
        )

        # Subparser for each Provider (ie: Mistral, OpenAI)
        parser_mistral = subparsers.add_parser(
            "mistral",
            help="Provides access to French/EU based AI models by Mistral AI.",
        )
        parser_openai = subparsers.add_parser(
            "openai",
            help="Provides access to American based AI models by OpenAI.",
        )
        subparser_modes_mistral = parser_mistral.add_subparsers(
            help="The modes available to Mistral AI.",
            dest="mode_name",
        )
        subparser_modes_openai = parser_openai.add_subparsers(
            help="The modes available to OpenAI.",
            dest="mode_name",
        )
        self.parser._subparsers.title = "commands"  # type: ignore[union-attr]

        add_common_mode_arguments(subparser_modes=subparser_modes_mistral, provider=ProviderNames.MISTRAL.value)
        add_common_mode_arguments(subparser_modes=subparser_modes_openai, provider=ProviderNames.OPENAI.value)

        # rename all subcommands of 'gptcli' from 'positional arguments' to 'commands' in the help doc
        subparsers_actions: list[argparse._SubParsersAction] = self._get_subparser_actions()  # type: ignore[type-arg]
        for subparsers_action in subparsers_actions:
            for _, subparser in subparsers_action.choices.items():
                subparser._subparsers.title = "commands"

        self.args = self.parser.parse_args()

    def configure_command_parser(self) -> None:
        """Used to run any final configurations we want regarding the argparse parameters."""
        logger.info("Running cli")
        self._configure_logging_level()

    def _configure_logging_level(self) -> None:
        logger.info("Configuring logging level")
        log_level = self.args.loglevel
        logging.basicConfig(level=log_level)

    def print_help(self) -> None:
        """Prints the help doc when the user types `gptcli`."""
        self.parser.print_help()

    def print_help_provider(self, provider: str) -> None:
        """Print the help doc when the user types `gptcli openai` or similar.

        In order to print the help doc for a subparser using argparse,
        we have to manually search for the subparser and use the format_help() function.
        This method does just that; given a `provider`.

        Args:
            provider (str): The name of the provider chosen by the user, for example `openai` or `mistral`.
        """

        # retrieve subparsers from parser
        subparsers_actions: list[Any] = self._get_subparser_actions()
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                if choice == provider:
                    print(subparser.format_help())
                    break

    def print_help_provider_mode(self) -> None:
        """Prints the help doc when the user types commands similar to `gptcli openai chat`."""
        self.parser.print_help()

    def _get_subparser_actions(self) -> list[argparse._SubParsersAction]:  # type: ignore[type-arg]
        return [action for action in self.parser._actions if isinstance(action, argparse._SubParsersAction)]
