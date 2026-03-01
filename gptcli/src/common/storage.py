"""Handles access and storage of messages and OCR results."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from glob import glob
from logging import Logger
from os import path
from time import time
from typing import Any
from urllib.parse import unquote, urlparse

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI

from gptcli.constants import (
    GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR,
)
from gptcli.src.common.constants import (
    GRN,
    GRY,
    MGA,
    MISTRAL,
    OPENAI,
    RED,
    RST,
    OpenaiUserRoles,
)
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.message import Message, MessageFactory, Messages
from gptcli.src.common.validators import InputType, is_url

logger: Logger = logging.getLogger(__name__)


class StorageEmpty(Exception):
    """Raised when attempting to read from storage that contains no files."""


class Storage:
    """Handles storage operations for chat messages and OCR results.

    This class provides methods to store and retrieve chat conversations
    and OCR processing results to/from the local filesystem. Data is stored
    in provider-specific directories under ~/.gptcli/.

    Attributes:
        _provider: The LLM provider name (e.g., 'mistral', 'openai').
        _json_dir: Directory path for storing chat JSON files.
        _ocr_dir: Directory path for storing OCR results.
    """

    _FALLBACK_MARKDOWN_FILENAME = "document.md"
    _ENCRYPTED_DATA_WITHOUT_KEY = "Encrypted data found but no encryption key provided."

    def __init__(self, provider: str, encryption: Encryption | None = None) -> None:
        """Initialize storage with provider-specific directories.

        Args:
            provider (str): The LLM provider name ('mistral' or 'openai').
            encryption (Encryption | None): Optional encryption instance for encrypting/decrypting stored data.

        Raises:
            NotImplementedError: If the provider is not supported.
        """
        self._provider: str = provider
        self._encryption: Encryption | None = encryption

        self._json_dir: str = ""
        self._ocr_dir: str = ""
        if self._provider == MISTRAL:
            self._json_dir = GPTCLI_PROVIDER_MISTRAL_STORAGE_JSON_DIR
            self._ocr_dir = GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR
        elif self._provider == OPENAI:
            self._json_dir = GPTCLI_PROVIDER_OPENAI_STORAGE_JSON_DIR
            self._ocr_dir = GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

    def _write_text(self, filepath: str, content: str) -> None:
        """Write text content to a file, encrypting if encryption is enabled.

        When encryption is enabled, writes to filepath + '.enc' in binary.
        Otherwise, writes plaintext to the given filepath.

        Args:
            filepath (str): The base filepath (without .enc suffix).
            content (str): The text content to write.
        """
        if self._encryption:
            encrypted: bytes = self._encryption.encrypt(content.encode("utf-8"))
            with open(filepath + ".enc", "wb") as fp:
                fp.write(encrypted)
        else:
            with open(filepath, "w", encoding="utf8") as fp:
                fp.write(content)

    def _read_text(self, filepath_plaintext: str, filepath_encrypted: str | None = None) -> str | None:
        """Read text content from a plaintext or encrypted file.

        Prefers the encrypted file when encryption is available. Returns None
        with a user-visible message when encrypted data is found without a key.

        Args:
            filepath_plaintext (str): Path to the plaintext file.
            filepath_encrypted (str | None): Path to the encrypted file. If None, derived as filepath_plaintext + '.enc'.

        Returns:
            str | None: The text content, or None if decryption fails or key is missing.
        """
        enc_path: str = filepath_encrypted if filepath_encrypted is not None else filepath_plaintext + ".enc"
        if os.path.exists(enc_path):
            if self._encryption is None:
                print_formatted_text(ANSI(f"{RED}>>>{RST} {self._ENCRYPTED_DATA_WITHOUT_KEY}"))
                return None
            decrypted: bytes | None = self._encryption.decrypt_file(enc_path)
            if decrypted is None:
                print_formatted_text(ANSI(f"{RED}>>>{RST} Failed to decrypt data."))
                return None
            return decrypted.decode("utf-8")
        if os.path.exists(filepath_plaintext):
            with open(filepath_plaintext, "r", encoding="utf8") as fp:
                return fp.read()
        return None

    def store_messages(self, messages: Messages) -> None:
        """Store a Messages collection to the local filesystem.

        Saves the messages as a JSON file with a timestamped filename
        in the provider's storage directory.

        Args:
            messages: A Messages collection containing Message objects to store.
        """
        logger.info("Storing Messages to local filesystem.")
        if len(messages) > 0:
            filepath = self._create_json_filepath()
            self._write_text(filepath, messages.to_json())

    def _create_json_filepath(self) -> str:
        """Generate a unique filepath for storing chat messages.

        Returns:
            A filepath in the format: {json_dir}/{epoch}__{datetime}__chat.json
        """
        epoch: str = str(int(time()))
        datetime_now_utc: str = datetime.now(tz=timezone.utc).strftime(r"_%Y_%m_%d__%H_%M_%S_")
        filename: str = "_".join([epoch, datetime_now_utc, "chat"]) + ".json"
        filepath: str = path.join(self._json_dir, filename)
        return filepath

    def _create_ocr_session_dir(self) -> str:
        """Generate a unique directory path for storing OCR results.

        Returns:
            A directory path in the format: {ocr_dir}/{epoch}__{datetime}__ocr
        """
        epoch: str = str(int(time()))
        datetime_now_utc: str = datetime.now(tz=timezone.utc).strftime(r"_%Y_%m_%d__%H_%M_%S_")
        folder_name: str = "_".join([epoch, datetime_now_utc, "ocr"])
        session_dir: str = path.join(self._ocr_dir, folder_name)
        return session_dir

    @staticmethod
    def extract_filename_from_source(source: str) -> str:
        """Extract the filename from a URL or filesystem path.

        Handles URL decoding for percent-encoded characters in URLs.

        Args:
            source: A URL (http/https) or filesystem path.

        Returns:
            The extracted filename, or empty string if no filename found.
        """
        if is_url(source):
            parsed = urlparse(source)
            url_path = unquote(parsed.path)
            return path.basename(url_path)
        else:
            return path.basename(source)

    @staticmethod
    def derive_markdown_filename_from_source(source: str) -> str:
        """Derive a Markdown filename from a source URL or filepath.

        Extracts the base filename and replaces its extension with .md.
        Falls back to 'document.md' if no filename can be derived.

        Args:
            source: A URL (http/https) or filesystem path to derive the name from.

        Returns:
            A filename with .md extension (e.g., 'report.pdf' -> 'report.md').

        Raises:
            ValueError: If source is empty or contains only whitespace.
        """
        if not source:
            raise ValueError("Source cannot be empty.")
        if not source.strip():
            raise ValueError("Source cannot be whitespace only.")

        source = source.strip()
        filename = Storage.extract_filename_from_source(source)

        if not filename:
            return Storage._FALLBACK_MARKDOWN_FILENAME

        if "." in filename and not filename.startswith("."):
            name, _ = filename.rsplit(".", 1)
            return f"{name}.md"
        else:
            return f"{filename}.md"

    def _build_ocr_metadata(
        self,
        source: str,
        model: str,
        page_count: int,
        markdown_file: str,
        images: list[str],
    ) -> dict[str, Any]:
        """Build a metadata dictionary for an OCR result.

        Args:
            source: The original input source (URL or filepath).
            model: The OCR model used for processing.
            page_count: Number of pages processed.
            markdown_file: Name of the generated Markdown file.
            images: List of generated image filenames.

        Returns:
            A dictionary containing source info, OCR processing details,
            and output file references.
        """
        input_type = InputType.URL.value if is_url(source) else InputType.FILEPATH.value
        filename = self.extract_filename_from_source(source)

        return {
            "source": {
                "input": source,
                "input_type": input_type,
                "filename": filename,
            },
            "ocr": {
                "created": time(),
                "uuid": str(uuid.uuid4()),
                "model": model,
                "provider": self._provider,
                "page_count": page_count,
            },
            "output": {
                "markdown_file": markdown_file,
                "images": images,
            },
        }

    def store_ocr_result(
        self,
        source: str,
        markdown_content: str,
        model: str,
        page_count: int,
        image_data: list[tuple[str, bytes]],
    ) -> str:
        """Store an OCR processing result to local storage.

        Creates a session directory containing:
        - A Markdown file with the extracted text
        - Any extracted images
        - A metadata.json file with processing details

        Args:
            source: The original input source (URL or filepath) that was processed.
            markdown_content: The extracted Markdown text content.
            model: The OCR model used for processing.
            page_count: Number of pages processed from the source.
            image_data: List of (filename, bytes) tuples for extracted images.

        Returns:
            The full path to the created session directory.
        """
        logger.info("Storing OCR result to local filesystem.")

        session_dir = self._create_ocr_session_dir()
        os.makedirs(session_dir, exist_ok=True)

        markdown_filename = self.derive_markdown_filename_from_source(source)
        markdown_filepath = path.join(session_dir, markdown_filename)
        self._write_text(markdown_filepath, markdown_content)

        # Get filename safely using os.path.basename() and realpath check.
        resolved_session_dir = os.path.realpath(session_dir)
        image_filenames: list[str] = []
        for filename, data in image_data:
            safe_filename = path.basename(filename)
            if not safe_filename:
                logger.warning("Possible malicious filename detected; path traversal.")
                logger.warning(f"Filename of: '{filename}'")
                continue
            image_filepath = path.join(session_dir, safe_filename)
            if not os.path.realpath(image_filepath).startswith(resolved_session_dir):
                logger.warning(f"Image path escapes session folder; skipping '{filename}'.")
                continue
            with open(image_filepath, "wb") as fp:
                fp.write(data)
            if self._encryption:
                self._encryption.encrypt_file(image_filepath)
            image_filenames.append(safe_filename)

        metadata = self._build_ocr_metadata(
            source=source,
            model=model,
            page_count=page_count,
            markdown_file=markdown_filename,
            images=image_filenames,
        )
        metadata_filepath = path.join(session_dir, "metadata.json")
        with open(metadata_filepath, "w", encoding="utf8") as fp:
            json.dump(metadata, fp, ensure_ascii=False)
        if self._encryption:
            self._encryption.encrypt_file(metadata_filepath)

        return session_dir

    def extract_last_ocr_result(self) -> str | None:
        """Extract the Markdown content from the most recent OCR session.

        Finds the newest session directory by epoch prefix in the directory
        name, locates the Markdown file within it, and returns its content.

        Returns:
            str: The Markdown content from the most recent OCR session.

        Raises:
            StorageEmpty: If no OCR sessions exist in storage.
        """
        logger.info("Extracting last OCR result from storage.")
        session_dirs: list[str] = glob(path.join(self._ocr_dir, "*__ocr"))

        if not session_dirs:
            raise StorageEmpty(f"No OCR sessions found in {self._ocr_dir}")

        last_session_dir: str = max(session_dirs, key=lambda p: path.basename(p))

        markdown_files: list[str] = sorted(glob(path.join(last_session_dir, "*.md")))
        markdown_enc_files: list[str] = sorted(glob(path.join(last_session_dir, "*.md.enc")))

        if not markdown_files and not markdown_enc_files:
            raise StorageEmpty(f"No markdown file found in {last_session_dir}")

        plaintext_path: str = markdown_files[0] if markdown_files else ""
        encrypted_path: str | None = markdown_enc_files[0] if markdown_enc_files else None

        if not plaintext_path and encrypted_path:
            plaintext_path = encrypted_path[: -len(".enc")]

        content: str | None = self._read_text(plaintext_path, encrypted_path)
        if content is None and not markdown_files and not markdown_enc_files:
            raise StorageEmpty(f"No readable markdown file found in {last_session_dir}")
        return content

    def display_last_ocr_result(self) -> None:
        """Extract and display the Markdown content from the most recent OCR session.

        Retrieves the last OCR result from storage and prints it to the
        terminal. Prints a warning if no OCR sessions exist.
        """
        logger.info("Extracting last OCR result from storage.")
        try:
            content: str | None = self.extract_last_ocr_result()
        except StorageEmpty:
            print_formatted_text(ANSI(f"{RED}>>>{RST} No OCR results found in storage; storage is likely empty."))
            return None

        if content is None:
            return None

        print(content)
        return None

    def extract_messages(self) -> Messages | None:
        """Extract messages from the most recent chat session.

        Finds the newest JSON file by epoch prefix in the filename
        and reconstructs the Messages collection.

        Returns:
            A Messages collection containing all messages from the last session.

        Raises:
            StorageEmpty: If no chat sessions exist in storage.
        """
        logger.info("Extracting messages from storage.")
        filepaths: list[str] = glob(path.expanduser(path.join(self._json_dir, "*.json")))
        filepaths += glob(path.expanduser(path.join(self._json_dir, "*.json.enc")))

        if not filepaths:
            raise StorageEmpty(f"No chat sessions found in {self._json_dir}")

        last_chat_session: str = max(filepaths, key=lambda p: path.basename(p))

        if last_chat_session.endswith(".enc"):
            plaintext_path: str = last_chat_session[: -len(".enc")]
            encrypted_path: str | None = last_chat_session
        else:
            plaintext_path = last_chat_session
            encrypted_path = None

        raw_content: str | None = self._read_text(plaintext_path, encrypted_path)
        if raw_content is None:
            return None
        file_contents_messages: list[dict[str, Any]] = json.loads(raw_content)["messages"]

        messages: Messages = Messages()
        for message in file_contents_messages:
            m: Message = MessageFactory.message_from_dict(message=message)
            messages.add(message=m)

        return messages

    def display_last_chat(self) -> None:
        """Extract, format, and display messages from the most recent chat session.

        Retrieves messages from storage, formats them with ANSI color codes,
        and prints them to the terminal. User messages are prefixed with
        green '>>>', model replies with magenta '>>>', errors or warnings
        with red '>>>'.
        """
        logger.info("Extracting messages from storage.")
        try:
            messages: Messages | None = self.extract_messages()
        except StorageEmpty:
            print_formatted_text(ANSI(f"{RED}>>>{RST} No chats found in storage; storage is likely empty."))
            return None

        if messages is None:
            return None

        for message in messages:
            if message.is_reply:
                print_formatted_text(ANSI(f"{MGA}>>>{RST} " + message.content.strip()))
            elif message.is_system:
                label: str = "dev" if message.role == OpenaiUserRoles.system_role() else "sys"
                print_formatted_text(ANSI(f"{GRY}[{label}]{RST} " + message.content.strip()))
            else:
                print_formatted_text(ANSI(f"{GRN}>>>{RST} " + message.content.strip()))

        return None
