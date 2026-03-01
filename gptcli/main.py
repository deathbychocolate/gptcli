"""The entrypoint to the project."""

import logging
import os
import sys
from argparse import Namespace
from logging import Logger

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL,
    GPTCLI_PROVIDER_MISTRAL_KEY_FILE,
    GPTCLI_PROVIDER_OPENAI,
    GPTCLI_PROVIDER_OPENAI_KEY_FILE,
    GPTCLI_ROOT_FILEPATH,
)
from gptcli.src.cli import CommandParser
from gptcli.src.common.constants import ModeNames, ProviderNames
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.key_management import KeyManager, make_key_manager
from gptcli.src.common.passphrase import PassphrasePrompt
from gptcli.src.install import Migrate, Mistral, Openai
from gptcli.src.modes.chat import ChatUser
from gptcli.src.modes.encryption_commands import EncryptionCommands
from gptcli.src.modes.nuke import Nuke
from gptcli.src.modes.optical_character_recognition import (
    OpticalCharacterRecognition,
)
from gptcli.src.modes.single_exchange import SingleExchange

logger: Logger = logging.getLogger(__name__)


def create_command_parser() -> CommandParser:
    logger.info("Running and configuring argparse.")
    parser: CommandParser = CommandParser()
    parser.configure_command_parser()
    return parser


_PROVIDER_DIRS: list[str] = [GPTCLI_PROVIDER_MISTRAL, GPTCLI_PROVIDER_OPENAI]


def _handle_all_provider_command(args: Namespace) -> None:
    """Handle commands that apply to all providers: encrypt, decrypt, rekey, and nuke.

    Args:
        args (Namespace): The parsed CLI arguments.
    """
    if args.mode_name == ModeNames.NUKE.value:
        Nuke.nuke(root_dir=GPTCLI_ROOT_FILEPATH)
        return None

    provider_dirs: list[str] = _PROVIDER_DIRS
    no_cache: bool = args.no_cache

    if args.mode_name == ModeNames.REKEY.value:
        encryption: Encryption | None = _load_encryption(no_cache=no_cache)
        if encryption is None:
            print("Encryption is not initialized. Nothing to rekey.")
            return None
        if not EncryptionCommands.rekey(old_encryption=encryption, providers=provider_dirs):
            sys.exit(1)
        return None

    km: KeyManager = make_key_manager(no_cache=no_cache)
    if args.mode_name == ModeNames.ENCRYPT.value:
        if not km.is_initialized():
            passphrase: str | None = PassphrasePrompt.create_with_confirmation()
            if passphrase is None:
                sys.exit(1)
            key: bytes = km.initialize(passphrase)
        else:
            loaded_key: bytes | None = km.load_key()
            if loaded_key is None:
                sys.exit(1)
            key = loaded_key
        enc = Encryption(key=key)
        for provider_dir in provider_dirs:
            cmd = EncryptionCommands(provider_dir=provider_dir, encryption=enc)
            cmd.encrypt_provider()
    elif args.mode_name == ModeNames.DECRYPT.value:
        enc_instance: Encryption | None = _load_encryption()
        if enc_instance is None:
            print("Encryption is not initialized. Nothing to decrypt.")
            return None
        print("Warning: Encryption at rest is enabled by default to protect your data.")
        print("Decrypting should only be done if you plan to migrate data to another platform.")
        print("Re-encrypt when done.")
        for provider_dir in provider_dirs:
            cmd = EncryptionCommands(provider_dir=provider_dir, encryption=enc_instance)
            cmd.decrypt_provider()

    return None


def _load_encryption(no_cache: bool = False) -> Encryption | None:
    """Load encryption if initialized, otherwise return None.

    Args:
        no_cache (bool): If True, disable encryption key caching.

    Returns:
        Encryption | None: An Encryption instance if encryption is initialized, None otherwise.
    """
    km: KeyManager = make_key_manager(no_cache=no_cache)
    if not km.is_initialized():
        return None
    key: bytes | None = km.load_key()
    if key is None:
        sys.exit(1)
    return Encryption(key=key)


def _key_file_for_provider(provider: str) -> str:
    """Map a provider name to its API key file path.

    Args:
        provider (str): The provider name (e.g., 'mistral', 'openai').

    Returns:
        str: The filesystem path to the provider's API key file.

    Raises:
        NotImplementedError: If the provider is not supported.
    """
    if provider == ProviderNames.MISTRAL.value:
        return GPTCLI_PROVIDER_MISTRAL_KEY_FILE
    elif provider == ProviderNames.OPENAI.value:
        return GPTCLI_PROVIDER_OPENAI_KEY_FILE
    else:
        raise NotImplementedError(f"Provider '{provider}' not yet supported.")


def _read_encrypted_key(filepath: str, encryption: Encryption) -> str:
    """Decrypt and return the API key from an encrypted key file.

    Args:
        filepath (str): Path to the encrypted key file.
        encryption (Encryption): Encryption instance for decryption.

    Returns:
        str: The decrypted API key, or empty string if decryption fails.
    """
    api_key_bytes: bytes | None = encryption.decrypt_file(filepath)
    if api_key_bytes is None:
        logger.warning("Failed to decrypt API key file.")
        return ""
    return api_key_bytes.decode("utf-8")


def _read_plaintext_key(filepath: str) -> str:
    """Read the API key from a plaintext key file.

    Args:
        filepath (str): Path to the plaintext key file.

    Returns:
        str: The API key, or empty string if the file is not found.
    """
    try:
        with open(filepath, "r", encoding="utf8") as fp:
            return fp.read()
    except FileNotFoundError:
        logger.warning("File storing API key not found. Skipping loading API from local storage.")
        return ""


def load_api_key(parser: CommandParser, encryption: Encryption | None = None) -> str:
    """Load the API key from CLI arguments, encrypted file, or plaintext file.

    Args:
        parser (CommandParser): The parsed CLI arguments.
        encryption (Encryption | None, optional): Encryption instance for decrypting stored keys. Defaults to None.

    Returns:
        str: The resolved API key, or empty string if not found.
    """
    logger.info("Loading API key.")

    file: str = _key_file_for_provider(parser.args.provider)

    if "key" in parser.args and parser.args.key is None:
        enc_file: str = file + ".enc"
        if os.path.exists(enc_file) and encryption:
            return _read_encrypted_key(enc_file, encryption)
        else:
            return _read_plaintext_key(file)
    elif "key" in parser.args and str(parser.args.key).isascii():
        return str(parser.args.key)

    return ""


def enter_single_exchange_mode(parser: CommandParser, api_key: str = "") -> None:
    logger.info("Entering CLI mode.")
    SingleExchange(
        input_string=parser.args.input_string,
        model=parser.args.model,
        provider=parser.args.provider,
        role_user=parser.args.role_user,
        role_model=parser.args.role_model,
        filepath=parser.args.filepath,
        output=parser.args.output,
        api_key=api_key,
    ).start()


def enter_chat_mode(parser: CommandParser, encryption: Encryption | None = None, api_key: str = "") -> None:
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
        encryption=encryption,
        api_key=api_key,
    ).start()


def enter_ocr_mode(parser: CommandParser, encryption: Encryption | None = None, api_key: str = "") -> None:
    logger.info("Entering OCR mode.")
    OpticalCharacterRecognition(
        model=parser.args.model,
        provider=parser.args.provider,
        store=parser.args.store,
        display_last=parser.args.display_last,
        display=parser.args.display,
        filelist=parser.args.filelist,
        output_dir=parser.args.output_dir,
        no_output_dir=parser.args.no_output_dir,
        inputs=parser.args.inputs,
        include_images=not parser.args.no_images,
        encryption=encryption,
        api_key=api_key,
    ).start()


def main() -> None:
    """This is the main function."""
    parser: CommandParser = create_command_parser()
    args: Namespace = parser.args

    # print help when ...
    if not args.provider:  # provider is missing
        parser.print_help()
        return None
    elif not args.mode_name:  # mode is missing
        args.parser.print_help()
        return None
    elif args.mode_name == ModeNames.OCR.value and not (args.inputs or args.filelist or args.display_last):
        parser.args.parser.print_help()
        return None

    # Handle encryption commands before install/API key loading
    if args.mode_name in ModeNames.all_provider_modes():
        _handle_all_provider_command(args)
        return None

    no_cache: bool = args.no_cache

    Migrate.migrate_legacy_tree()
    Migrate.to_encrypted(no_cache=no_cache)

    # install
    match parser.args.provider:
        case ProviderNames.MISTRAL.value:
            Mistral(no_cache=no_cache).install()
        case ProviderNames.OPENAI.value:
            Openai(no_cache=no_cache).install()
        case _:
            raise NotImplementedError(f"Provider '{parser.args.provider}' not yet supported.")

    encryption: Encryption | None = _load_encryption(no_cache=no_cache)

    api_key: str = load_api_key(parser=parser, encryption=encryption)

    match parser.args.mode_name:
        case ModeNames.SE.value:
            enter_single_exchange_mode(parser=parser, api_key=api_key)
        case ModeNames.CHAT.value:
            enter_chat_mode(parser=parser, encryption=encryption, api_key=api_key)
        case ModeNames.OCR.value:
            enter_ocr_mode(parser=parser, encryption=encryption, api_key=api_key)

    return None


if __name__ == "__main__":
    main()
