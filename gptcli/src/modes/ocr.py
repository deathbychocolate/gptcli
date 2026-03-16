"""Contains the code needed to perform optical character recognition.

Optical Character Recognition (OCR) allows the user to convert files
such as images (png, jpeg) or PDFs or others into base64 encoded files
which are sent to OCR specific models to be converted into Markdown text.

The file as a result becomes suitable for consumption by non-OCR models.
"""

import base64
import hashlib
import json
import logging
import os
from logging import Logger

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import ANSI
from requests import Response, post
from requests.exceptions import RequestException

from gptcli.src.common.api import recognizing_spinner
from gptcli.src.common.constants import (
    GRN,
    MISTRAL,
    OPENAI,
    RST,
    DuplicateAction,
)
from gptcli.src.common.decorators import user_triggered_abort
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.storage import Storage
from gptcli.src.common.validators import InputType, classify_input

logger: Logger = logging.getLogger(__name__)


class OpticalCharacterRecognition:

    def __init__(
        self,
        model: str,
        provider: str,
        store: bool,
        display_last: bool,
        display: bool,
        filelist: str,
        output_dir: str,
        no_output_dir: bool,
        inputs: list[str],
        include_images: bool = True,
        encryption: Encryption | None = None,
        api_key: str = "",
        on_duplicate: str = "",
    ):
        """Initialize an OCR session for converting documents to Markdown.

        Args:
            model (str): The OCR model to use for document conversion.
            provider (str): The API provider name (e.g., 'mistral').
            store (bool): Whether to store the OCR results locally.
            display_last (bool): Whether to display the last OCR session from storage.
            display (bool): Whether to display the OCR result to stdout.
            filelist (str): Path to a file containing a list of documents to process.
            output_dir (str): Directory path for saving converted Markdown files.
            no_output_dir (bool): Whether to disable saving converted Markdown files to output_dir.
            inputs (list[str]): List of filepaths or URLs of documents to convert.
            include_images (bool, optional): Whether to extract images from OCR responses. Defaults to True.
            encryption (Encryption | None, optional): Encryption instance for encrypting stored data. Defaults to None.
            api_key (str, optional): The API key for authentication. Defaults to "".
            on_duplicate (str, optional): Action when duplicate document found. One of "use", "overwrite", "new", "skip", or "" for interactive prompt. Defaults to "".
        """
        self._model: str = model
        self._provider: str = provider
        self._store: bool = store
        self._display_last: bool = display_last
        self._display: bool = display
        self._filelist: str = filelist
        self._output_dir: str | None = None if no_output_dir else output_dir
        self._inputs: list[str] = inputs
        self._include_images: bool = include_images
        self._on_duplicate: str = on_duplicate

        self._storage: Storage = Storage(provider=provider, encryption=encryption)

        self._api_key: str = api_key
        self._ocr_endpoint: str = ""
        if provider == MISTRAL:
            self._ocr_endpoint = "https://api.mistral.ai/v1/ocr"
        elif provider == OPENAI:
            self._ocr_endpoint = ""  # TODO: Add OpenAI OCR endpoint when available
        else:
            raise NotImplementedError(f"Provider '{provider}' is not yet supported for OCR.")

    @user_triggered_abort
    def start(self) -> None:
        """Send a list of filepaths and/or URLs and receive Markdown text."""
        logger.info("Starting Optical Character Recognition.")

        if self._display_last:
            self._storage.display_last_ocr_result()
            return None

        self._validate_output_dir()

        for document in self._inputs:
            self._generate_markdown_from(document=document)

        if self._filelist:
            with open(self._filelist, "r", encoding="utf8") as fp:
                for line in fp:
                    if document := line.strip():
                        self._generate_markdown_from(document=document)

    def _generate_markdown_from(self, document: str) -> None:
        """Perform OCR on a document and optionally store/display the result.

        Checks for duplicate documents by fingerprint. When a duplicate is found,
        the action is determined by ``--on-duplicate`` (or interactive prompt).

        Args:
            document (str): The filepath or URL of the document to process.
        """
        input_type = classify_input(document)

        if input_type == InputType.UNSUPPORTED:
            logger.warning("Detected unsupported input type, it is likely neither a URL nor a valid filepath.")
            logger.warning(f"Skipping '{document}'.")
            return None

        content_hash = self._get_document_fingerprint(document, input_type)

        # Check for existing sessions with same hash
        existing_sessions = self._storage.find_ocr_sessions_by_hash(content_hash)

        if existing_sessions:
            action = self._on_duplicate if self._on_duplicate else self._prompt_for_duplicate_document(document)

            if action == DuplicateAction.SKIP.value:
                logger.info(f"Skipping document {document} as requested.")
                return None

            if action == DuplicateAction.USE.value:
                latest_session = existing_sessions[0]
                session_data = self._storage.load_ocr_session_data(latest_session)
                if session_data is None:
                    logger.warning(f"Failed to load cached OCR result for {document}.")
                    return None
                document_as_markdown, image_data, _ = session_data
                logger.info(f"Using existing OCR result for {document} (session: {latest_session}).")
                self._output_result(document, document_as_markdown, image_data)
                return None

            if action == DuplicateAction.OVERWRITE.value:
                document_as_markdown, image_data, page_count = self._perform_ocr(document, input_type)
                if self._store:
                    session_uuid = existing_sessions[0]
                    self._storage.overwrite_ocr_result(
                        session_uuid=session_uuid,
                        source=document,
                        markdown_content=document_as_markdown,
                        model=self._model,
                        page_count=page_count,
                        image_data=image_data,
                        content_hash=content_hash,
                    )
                self._output_result(document, document_as_markdown, image_data)
                return None

            # action == "new": fall through to normal OCR + store below

        # New document (or "new" action for duplicate)
        document_as_markdown, image_data, page_count = self._perform_ocr(document, input_type)

        if self._store:
            session_dir = self._storage.store_ocr_result(
                source=document,
                markdown_content=document_as_markdown,
                model=self._model,
                page_count=page_count,
                image_data=image_data,
                content_hash=content_hash,
            )
            logger.info(f"Stored OCR result to: {session_dir}")

        self._output_result(document, document_as_markdown, image_data)

        return None

    def _output_result(self, document: str, markdown_content: str, image_data: list[tuple[str, bytes]]) -> None:
        """Write OCR result to output directory and optionally display it.

        Args:
            document (str): The original source document path or URL.
            markdown_content (str): The extracted Markdown text content.
            image_data (list[tuple[str, bytes]]): List of (filename, bytes) tuples for extracted images.
        """
        self._write_to_output_dir(document=document, markdown_content=markdown_content, image_data=image_data)

        if self._display:
            print(markdown_content)

    def _perform_ocr(self, document: str, input_type: InputType) -> tuple[str, list[tuple[str, bytes]], int]:
        """Route OCR processing based on input type.

        Args:
            document (str): The filepath or URL of the document.
            input_type (InputType): The classified input type.

        Returns:
            tuple[str, list[tuple[str, bytes]], int]: Markdown content, image data, and page count.
        """
        if input_type == InputType.URL:
            return self._perform_ocr_from_url(url=document)
        return self._perform_ocr_from_filepath(filepath=document)

    def _validate_output_dir(self) -> None:
        """Validate that the output directory path is usable and create it if missing.

        Does nothing when output_dir is None (output writing disabled).

        Raises:
            ValueError: If the path exists but is not a directory, or cannot be created.
        """
        if self._output_dir is None:
            return None

        if os.path.exists(self._output_dir) and not os.path.isdir(self._output_dir):
            raise ValueError(f"Output path '{self._output_dir}' exists but is not a directory.")

        try:
            os.makedirs(self._output_dir, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create output directory '{self._output_dir}': {e}") from e

        return None

    def _write_to_output_dir(
        self,
        document: str,
        markdown_content: str,
        image_data: list[tuple[str, bytes]],
    ) -> None:
        """Write OCR results to the output directory.

        Creates a subfolder named after the provider and source document,
        containing the Markdown file and any extracted images. The pattern
        is `gptcli__{provider}__ocr__{document}` and an example subfolder
        name could be `gptcli__mistral__ocr__invoice`.

        Args:
            document (str): The original source document path or URL.
            markdown_content (str): The extracted Markdown text content.
            image_data (list[tuple[str, bytes]]): List of (filename, bytes) tuples for extracted images.
        """
        if self._output_dir is None:
            return None

        folder_name = Storage._derive_folder_name_from_source(self._provider, document)
        folder_path = os.path.join(self._output_dir, folder_name)
        folder_path = Storage._resolve_folder_collision(folder_path)
        os.makedirs(folder_path, exist_ok=True)

        markdown_filename = Storage.derive_markdown_filename_from_source(document)
        markdown_filepath = os.path.join(folder_path, markdown_filename)
        with open(markdown_filepath, "w", encoding="utf8") as fp:
            fp.write(markdown_content)

        resolved_folder_path = os.path.realpath(folder_path)
        for filename, data in image_data:
            safe_filename = os.path.basename(filename)
            if not safe_filename:
                logger.warning("Possible malicious filename detected; path traversal.")
                logger.warning(f"Filename of: '{filename}'")
                continue
            image_filepath = os.path.join(folder_path, safe_filename)
            if not os.path.realpath(image_filepath).startswith(resolved_folder_path):
                logger.warning(f"Image path escapes output folder; skipping '{filename}'.")
                continue
            with open(image_filepath, "wb") as fp:
                fp.write(data)

        abs_path: str = str(os.path.abspath(folder_path))
        print(f"OCR result saved to '{abs_path}'.")

        return None

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the OCR API request.

        Returns:
            dict[str, str]: Headers dictionary containing authorization and content-type.

        Raises:
            ValueError: If the API key is not set.
        """
        if not self._api_key:
            raise ValueError("API key is not set.")
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }

    def _get_document_fingerprint(self, document: str, input_type: InputType | None = None) -> str:
        """Generate a unique fingerprint for a document based on its content or URL.

        For URLs: uses the URL itself as the fingerprint (two different documents
        at the same URL will be treated as duplicates).
        For files: uses a SHA-256 hash of the file content as the fingerprint.

        Args:
            document (str): The filepath or URL of the document.
            input_type (InputType | None): Pre-classified input type. If None, classification is performed internally.

        Returns:
            str: A unique fingerprint string for the document.

        Raises:
            FileNotFoundError: If the local file does not exist (raised by ``open()``).
            ValueError: If the document type is unsupported.
        """
        if input_type is None:
            input_type = classify_input(document)

        if input_type == InputType.URL:
            return document

        if input_type == InputType.FILEPATH:
            hash_obj = hashlib.sha256()
            with open(document, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return f"file:{hash_obj.hexdigest()}"

        raise ValueError(f"Unsupported input type for fingerprinting: {document}")

    def _prompt_for_duplicate_document(self, document: str) -> str:
        """Prompt the user for action when a duplicate document is found.

        Args:
            document (str): The document path or URL.

        Returns:
            str: The user's choice: 'use', 'overwrite', 'new', or 'skip'.
        """
        choice_use: tuple[str, str] = ("1", DuplicateAction.USE.value)
        choice_overwrite: tuple[str, str] = ("2", DuplicateAction.OVERWRITE.value)
        choice_new: tuple[str, str] = ("3", DuplicateAction.NEW.value)
        choice_skip: tuple[str, str] = ("4", DuplicateAction.SKIP.value)
        choices = [*choice_use, *choice_overwrite, *choice_new, *choice_skip]

        print(f"\nDocument '{document}' has already been processed.")
        print("\nChoose an action:")
        print(f"  1 | {DuplicateAction.USE.value:<10}  Use existing cached result.")
        print(f"  2 | {DuplicateAction.OVERWRITE.value:<10}  Overwrite existing session with new OCR.")
        print(f"  3 | {DuplicateAction.NEW.value:<10}  Create new session alongside existing.")
        print(f"  4 | {DuplicateAction.SKIP.value:<10}  Skip this document.")
        print("\nTip: use --on-duplicate to automate this choice.")
        print("Tip: prefix '!' to apply to all remaining (e.g. '!1' or '!use').")

        completer = WordCompleter(choices, ignore_case=True)

        while True:
            try:
                raw_choice = prompt(message=ANSI(f"{GRN}>>>{RST} "), completer=completer).strip().lower()
                persist = raw_choice.startswith("!")
                choice = raw_choice.lstrip("!")

                action = ""
                if choice in choice_use:
                    action = DuplicateAction.USE.value
                elif choice in choice_overwrite:
                    action = DuplicateAction.OVERWRITE.value
                elif choice in choice_new:
                    action = DuplicateAction.NEW.value
                elif choice in choice_skip:
                    action = DuplicateAction.SKIP.value
                else:
                    print("Invalid choice. Please enter 1-4 or the action name.")
                    continue

                if persist:
                    self._on_duplicate = action

                return action
            except (EOFError, KeyboardInterrupt):
                return DuplicateAction.SKIP.value

    def _encode_pdf_to_base64(self, filepath: str) -> str:
        """Encode a PDF file to a base64 string.

        Args:
            filepath (str): Path to the PDF file to encode.

        Returns:
            str: The base64-encoded contents of the file as a UTF-8 string.
        """
        with open(filepath, "rb") as fp:
            return base64.b64encode(fp.read()).decode("utf8")

    def _make_ocr_request(
        self, headers: dict[str, str], content: dict[str, str | bool | dict[str, str | None]], label: str = ""
    ) -> Response | None:
        """Make an OCR API request, returning None on network or HTTP failure.

        Args:
            headers (dict[str, str]): HTTP headers for the request.
            content (dict): JSON payload for the OCR API.
            label (str, optional): Human-readable document identifier shown in the spinner. Defaults to empty string.

        Returns:
            Response | None: The Response object if successful, None if the request failed.
        """
        try:
            recognizing_spinner.label = f"Recognizing '{label}'"
            with recognizing_spinner:
                response = post(url=self._ocr_endpoint, headers=headers, json=content, timeout=30)
            return response if response.ok else None
        except RequestException:
            return None

    def _parse_ocr_response(self, response: Response) -> tuple[str, list[tuple[str, bytes]], int]:
        """Parse the OCR API response and extract Markdown content and images.

        Args:
            response (Response): The HTTP response from the OCR API.

        Returns:
            tuple[str, list[tuple[str, bytes]], int]: A tuple containing:
                - The document content as Markdown string.
                - A list of tuples with (image_id, image_bytes) for extracted images.
                - The total page count.

        Raises:
            ValueError: If the response contains invalid JSON or unexpected structure.
        """
        try:
            content = json.loads(response.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OCR API: {e}") from e

        if "pages" not in content or not isinstance(content["pages"], list):
            raise ValueError("Unexpected OCR response structure: missing or invalid 'pages' field.")

        image_data_list: list[tuple[str, bytes]] = []
        markdown_parts: list[str] = []

        pages = content["pages"]
        for page in pages:
            page_index = page["index"] + 1
            page_markdown = page["markdown"]
            markdown_parts.append(f"### Page {page_index}\n{page_markdown}")
            if self._include_images:
                for image in page["images"]:
                    image_bytes = base64.b64decode(image["image_base64"].split(",", maxsplit=1)[1])
                    image_data_list.append((image["id"], image_bytes))

        document_as_markdown = "\n\n".join(markdown_parts)
        return document_as_markdown, image_data_list, len(pages)

    def _perform_ocr_from_url(self, url: str) -> tuple[str, list[tuple[str, bytes]], int]:
        """Perform OCR on a document from a URL.

        Args:
            url (str): The URL of the document to process.

        Returns:
            tuple[str, list[tuple[str, bytes]], int]: A tuple containing the markdown content,
                image data, and page count.

        Raises:
            RuntimeError: If both document and image OCR requests fail.
        """
        headers: dict[str, str] = self._build_headers()

        content_pdf: dict[str, str | bool | dict[str, str | None]] = {
            "model": self._model,
            "document": {
                "type": "document_url",
                "document_url": url,
            },
            "include_image_base64": self._include_images,
        }

        content_img: dict[str, str | bool | dict[str, str | None]] = {
            "model": self._model,
            "document": {
                "type": "image_url",
                "image_url": url,
            },
        }

        response = self._make_ocr_request(headers, content_pdf, label=url)
        if response is None:
            logger.warning("Document request failed, trying as image.")
            response = self._make_ocr_request(headers, content_img, label=url)

        if response is None:
            raise RuntimeError(f"OCR request failed for URL: {url}")

        return self._parse_ocr_response(response)

    def _perform_ocr_from_filepath(self, filepath: str) -> tuple[str, list[tuple[str, bytes]], int]:
        """Perform OCR on a local file.

        Args:
            filepath (str): The path to the local file to process.

        Returns:
            tuple[str, list[tuple[str, bytes]], int]: A tuple containing the markdown content,
                image data, and page count.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            RuntimeError: If the OCR request fails.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        headers: dict[str, str] = self._build_headers()

        pdf_base64: str = self._encode_pdf_to_base64(filepath)
        content_pdf_local: dict[str, str | bool | dict[str, str | None]] = {
            "model": self._model,
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}",
            },
            "include_image_base64": self._include_images,
        }

        response = self._make_ocr_request(headers, content_pdf_local, label=filepath)
        if response is None:
            raise RuntimeError(f"OCR request failed for file: {filepath}")

        return self._parse_ocr_response(response)
