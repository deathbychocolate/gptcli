"""Handles access and storage of messages and OCR results."""

import json
import logging
import os
import uuid
from logging import Logger
from os import path
from time import time
from typing import Any
from urllib.parse import unquote, urlparse

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import ANSI

from gptcli.constants import (
    GPTCLI_MANIFEST_FILENAME,
    GPTCLI_METADATA_FILENAME,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR,
    GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR,
    GPTCLI_SESSION_FILENAME,
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
from gptcli.src.common.file_io import read_text_file
from gptcli.src.common.message import MessageFactory, Messages
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
        _chat_dir: Directory path for storing chat sessions.
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

        self._chat_dir: str = ""
        self._ocr_dir: str = ""
        if self._provider == MISTRAL:
            self._chat_dir = GPTCLI_PROVIDER_MISTRAL_STORAGE_CHAT_DIR
            self._ocr_dir = GPTCLI_PROVIDER_MISTRAL_STORAGE_OCR_DIR
        elif self._provider == OPENAI:
            self._chat_dir = GPTCLI_PROVIDER_OPENAI_STORAGE_CHAT_DIR
            self._ocr_dir = GPTCLI_PROVIDER_OPENAI_STORAGE_OCR_DIR
        else:
            raise NotImplementedError(f"Provider '{self._provider}' not yet supported.")

    @property
    def chat_dir(self) -> str:
        """The directory where chat sessions are stored."""
        return self._chat_dir

    def _write_image(self, filepath: str, data: bytes) -> None:
        """Write image data to a file, encrypting if encryption is enabled.

        When encryption is enabled, writes to filepath + '.enc' in binary.
        Otherwise, writes raw bytes to the given filepath.

        Args:
            filepath (str): The base filepath (without .enc suffix).
            data (bytes): The image data to write.
        """
        if self._encryption:
            encrypted: bytes = self._encryption.encrypt(data)
            with open(filepath + ".enc", "wb") as fp:
                fp.write(encrypted)
        else:
            with open(filepath, "wb") as fp:
                fp.write(data)

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
        return read_text_file(filepath_plaintext, self._encryption)

    # ── Manifest operations ──────────────────────────────────────────

    def _read_manifest(self, storage_dir: str) -> list[dict[str, Any]]:
        """Read the manifest from a storage directory.

        Args:
            storage_dir (str): The storage directory containing the manifest.

        Returns:
            list[dict[str, Any]]: List of manifest entries, each with 'uuid' and 'created' keys.
                Returns an empty list if the manifest does not exist.
        """
        content = self._read_text(path.join(storage_dir, GPTCLI_MANIFEST_FILENAME))
        if content is None:
            return []
        result: list[dict[str, Any]] = json.loads(content)
        return result

    def _write_manifest(self, storage_dir: str, entries: list[dict[str, Any]]) -> None:
        """Write the manifest to a storage directory.

        Args:
            storage_dir (str): The storage directory to write the manifest to.
            entries (list[dict[str, Any]]): List of manifest entries to write.
        """
        self._write_text(path.join(storage_dir, GPTCLI_MANIFEST_FILENAME), json.dumps(entries, ensure_ascii=False))

    def _append_to_manifest(self, storage_dir: str, session_uuid: str, created: float) -> None:
        """Append a new entry to the manifest in a storage directory.

        Non-atomic read-modify-write: acceptable for a single-user CLI.

        Args:
            storage_dir (str): The storage directory containing the manifest.
            session_uuid (str): The UUID of the new session.
            created (float): The creation timestamp (epoch seconds).
        """
        entries = self._read_manifest(storage_dir)
        entries.append({"uuid": session_uuid, "created": created})
        self._write_manifest(storage_dir, entries)

    def _prune_deleted_sessions(self, storage_dir: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove manifest entries whose session directory no longer exists on disk.

        Args:
            storage_dir (str): The storage directory containing the session subdirectories.
            entries (list[dict[str, Any]]): The current manifest entries.

        Returns:
            list[dict[str, Any]]: Entries filtered to only those with an existing session directory.
        """
        valid_entries = [e for e in entries if os.path.isdir(path.join(storage_dir, e["uuid"]))]
        if len(valid_entries) < len(entries):
            self._write_manifest(storage_dir, valid_entries)
        return valid_entries

    def _find_latest_uuid(self, storage_dir: str) -> str | None:
        """Find the UUID of the most recently created session.

        Args:
            storage_dir (str): The storage directory to search.

        Returns:
            str | None: The UUID with the highest 'created' timestamp, or None if no valid entries exist.
        """
        entries = self._prune_deleted_sessions(storage_dir, self._read_manifest(storage_dir))
        if not entries:
            return None
        latest = max(entries, key=lambda e: e["created"])
        uuid: str = latest["uuid"]
        return uuid

    # ── Session directory creation ───────────────────────────────────

    def _create_session_dir(self, base_dir: str) -> tuple[str, str, float]:
        """Create a new UUID-based session directory.

        Args:
            base_dir (str): The parent storage directory (chat_dir or ocr_dir).

        Returns:
            tuple[str, str, float]: A tuple of (session_dir_path, uuid_string, created_timestamp).
        """
        session_uuid = str(uuid.uuid4())
        created = time()
        session_dir = path.join(base_dir, session_uuid)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir, session_uuid, created

    # ── Chat session storage ─────────────────────────────────────────

    @staticmethod
    def build_chat_metadata(session_uuid: str, created: float, model: str, provider: str) -> dict[str, Any]:
        """Build a metadata dictionary for a chat session.

        Args:
            session_uuid (str): The UUID of the chat session.
            created (float): The creation timestamp (epoch seconds).
            model (str): The model used for the chat session.
            provider (str): The provider name.

        Returns:
            dict[str, Any]: A dictionary containing chat session metadata.
        """
        return {
            "chat": {
                "created": created,
                "uuid": session_uuid,
                "model": model,
                "provider": provider,
            }
        }

    def store_messages(self, messages: Messages, model: str = "") -> None:
        """Store a Messages collection to the local filesystem.

        Creates a UUID-based directory containing session.json and metadata.json,
        and updates the chat manifest.

        Args:
            messages (Messages): A Messages collection containing Message objects to store.
            model (str): The model used for the chat session.
        """
        logger.info("Storing Messages to local filesystem.")
        if len(messages) > 0:
            session_dir, session_uuid, created = self._create_session_dir(self._chat_dir)
            session_filepath = path.join(session_dir, GPTCLI_SESSION_FILENAME)
            self._write_text(session_filepath, messages.to_json())

            metadata = self.build_chat_metadata(session_uuid, created, model, self._provider)
            metadata_filepath = path.join(session_dir, GPTCLI_METADATA_FILENAME)
            self._write_text(metadata_filepath, json.dumps(metadata, ensure_ascii=False))

            self._append_to_manifest(self._chat_dir, session_uuid, created)

    # ── OCR session storage ──────────────────────────────────────────

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
        session_uuid: str,
        created: float,
    ) -> dict[str, Any]:
        """Build a metadata dictionary for an OCR result.

        Args:
            source (str): The original input source (URL or filepath).
            model (str): The OCR model used for processing.
            page_count (int): Number of pages processed.
            markdown_file (str): Name of the generated Markdown file.
            images (list[str]): List of generated image filenames.
            session_uuid (str): The UUID of the OCR session.
            created (float): The creation timestamp (epoch seconds).

        Returns:
            dict[str, Any]: A dictionary containing source info, OCR processing details,
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
                "created": created,
                "uuid": session_uuid,
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

        Creates a UUID-based session directory containing:
        - A Markdown file with the extracted text
        - Any extracted images
        - A metadata.json file with processing details

        Updates the OCR manifest with the new session entry.

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

        session_dir, session_uuid, created = self._create_session_dir(self._ocr_dir)

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
            self._write_image(image_filepath, data)
            image_filenames.append(safe_filename)

        metadata = self._build_ocr_metadata(
            source=source,
            model=model,
            page_count=page_count,
            markdown_file=markdown_filename,
            images=image_filenames,
            session_uuid=session_uuid,
            created=created,
        )
        metadata_filepath = path.join(session_dir, GPTCLI_METADATA_FILENAME)
        self._write_text(metadata_filepath, json.dumps(metadata, ensure_ascii=False))

        self._append_to_manifest(self._ocr_dir, session_uuid, created)

        return session_dir

    def extract_last_ocr_result(self) -> str | None:
        """Extract the Markdown content from the most recent OCR session.

        Uses the manifest to find the latest session UUID, then reads
        the Markdown file from that session directory.

        Returns:
            str: The Markdown content from the most recent OCR session.

        Raises:
            StorageEmpty: If no OCR sessions exist in storage.
        """
        logger.info("Extracting last OCR result from storage.")
        latest_uuid = self._find_latest_uuid(self._ocr_dir)
        if latest_uuid is None:
            raise StorageEmpty(f"No OCR sessions found in {self._ocr_dir}")

        session_dir = path.join(self._ocr_dir, latest_uuid)

        # Single listdir call, partition into plaintext and encrypted markdown files
        all_files = os.listdir(session_dir)
        markdown_enc_files: list[str] = sorted(f for f in all_files if f.endswith(".md.enc"))
        markdown_files: list[str] = sorted(f for f in all_files if f.endswith(".md") and not f.endswith(".md.enc"))

        if not markdown_files and not markdown_enc_files:
            raise StorageEmpty(f"No markdown file found in {session_dir}")

        plaintext_path: str = path.join(session_dir, markdown_files[0]) if markdown_files else ""
        encrypted_path: str | None = path.join(session_dir, markdown_enc_files[0]) if markdown_enc_files else None

        if not plaintext_path and encrypted_path:
            plaintext_path = encrypted_path[: -len(".enc")]

        content: str | None = self._read_text(plaintext_path, encrypted_path)
        if content is None and not markdown_files and not markdown_enc_files:
            raise StorageEmpty(f"No readable markdown file found in {session_dir}")
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

    @staticmethod
    def _parse_messages(raw_content: str) -> Messages:
        """Parse a JSON session file into a Messages collection.

        Args:
            raw_content (str): The raw JSON string from session.json.

        Returns:
            Messages: A Messages collection built from the JSON data.
        """
        messages: Messages = Messages()
        for message in json.loads(raw_content)["messages"]:
            messages.add(MessageFactory.message_from_dict(message=message))
        return messages

    def extract_messages(self) -> Messages | None:
        """Extract messages from the most recent chat session.

        Uses the manifest to find the latest session UUID, then reads
        session.json from that directory.

        Returns:
            A Messages collection containing all messages from the last session.

        Raises:
            StorageEmpty: If no chat sessions exist in storage.
        """
        logger.info("Extracting messages from storage.")
        latest_uuid = self._find_latest_uuid(self._chat_dir)
        if latest_uuid is None:
            raise StorageEmpty(f"No chat sessions found in {self._chat_dir}")

        session_file = path.join(self._chat_dir, latest_uuid, GPTCLI_SESSION_FILENAME)
        raw_content: str | None = self._read_text(session_file)
        if raw_content is None:
            return None
        return self._parse_messages(raw_content)

    def extract_messages_by_uuid(self, session_uuid: str) -> Messages | None:
        """Extract messages from a specific chat session by UUID.

        Args:
            session_uuid (str): The UUID of the chat session to load.

        Returns:
            Messages | None: A Messages collection, or None if the file is unreadable.

        Raises:
            StorageEmpty: If no session directory exists for the given UUID.
        """
        session_dir = path.join(self._chat_dir, session_uuid)
        if not os.path.isdir(session_dir):
            raise StorageEmpty(f"No chat session found for UUID {session_uuid}")

        session_file = path.join(session_dir, GPTCLI_SESSION_FILENAME)
        raw_content: str | None = self._read_text(session_file)
        if raw_content is None:
            return None
        return self._parse_messages(raw_content)

    def read_session_model(self, session_uuid: str) -> str | None:
        """Read the model name from a session's metadata file.

        Args:
            session_uuid (str): The UUID of the chat session.

        Returns:
            str | None: The model name, or None if the metadata is unreadable.
        """
        session_dir = path.join(self._chat_dir, session_uuid)
        metadata_file = path.join(session_dir, GPTCLI_METADATA_FILENAME)
        raw_content: str | None = self._read_text(metadata_file)
        if raw_content is None:
            return None
        try:
            metadata: dict[str, Any] = json.loads(raw_content)
            model: str = metadata.get("chat", {}).get("model", "")
            return model or None
        except (json.JSONDecodeError, AttributeError):
            return None

    @staticmethod
    def _display_messages(messages: Messages) -> None:
        """Format and display a collection of chat messages with ANSI color codes.

        Args:
            messages (Messages): The messages to display.
        """
        for message in messages:
            if message.is_reply:
                print_formatted_text(ANSI(f"{MGA}>>>{RST} " + message.content.strip()))
            elif message.is_system:
                label: str = "dev" if message.role == OpenaiUserRoles.system_role() else "sys"
                print_formatted_text(ANSI(f"{GRY}[{label}]{RST} " + message.content.strip()))
            else:
                print_formatted_text(ANSI(f"{GRN}>>>{RST} " + message.content.strip()))

    def display_chat_by_uuid(self, session_uuid: str) -> None:
        """Extract, format, and display messages from a specific chat session.

        Args:
            session_uuid (str): The UUID of the chat session to display.
        """
        try:
            messages: Messages | None = self.extract_messages_by_uuid(session_uuid)
        except StorageEmpty:
            print_formatted_text(ANSI(f"{RED}>>>{RST} No chat session found for UUID {session_uuid}."))
            return None

        if messages is None:
            return None

        self._display_messages(messages)
        return None

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

        self._display_messages(messages)
        return None
