"""Contains the code needed to perform optical character recognition.

Optical Character Recognition (OCR) allows the user to convert files
such as images (png, jpeg) or PDFs or others into base64 encoded files
which are sent to OCR specific models to be converted into Markdown text.

The file as a result becomes suitable for consumption by non-OCR models.
"""

import base64
import json
import logging
import os
from logging import Logger
from os import environ

from requests import Response, post
from requests.exceptions import RequestException

from gptcli.constants import MISTRAL_API_KEY, OPENAI_API_KEY
from gptcli.src.common.constants import MISTRAL, OPENAI
from gptcli.src.common.decorators import user_triggered_abort
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
        inputs: list[str],
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
            inputs (list[str]): List of filepaths or URLs of documents to convert.
        """
        self._model: str = model
        self._provider: str = provider
        self._store: bool = store
        self._display_last: bool = display_last  # TODO: implement
        self._display: bool = display
        self._filelist: str = filelist  # TODO: implement
        self._output_dir: str = output_dir  # TODO: implement
        self._inputs: list[str] = inputs

        self._storage: Storage = Storage(provider=provider)

        self._api_key: str = ""
        self._ocr_endpoint: str = ""
        if provider == MISTRAL:
            self._api_key = MISTRAL_API_KEY
            self._ocr_endpoint = "https://api.mistral.ai/v1/ocr"
        elif provider == OPENAI:
            self._api_key = OPENAI_API_KEY
            self._ocr_endpoint = ""  # TODO: Add OpenAI OCR endpoint when available
        else:
            raise NotImplementedError(f"Provider '{provider}' is not yet supported for OCR.")

    @user_triggered_abort
    def start(self) -> None:
        """Send a list of filepaths and/or URLs and receive Markdown text."""
        logger.info("Starting Optical Character Recognition.")

        for document in self._inputs:
            input_type = classify_input(document)
            if input_type == InputType.URL:
                document_as_markdown, image_data, page_count = self._perform_ocr_from_url(url=document)
            elif input_type == InputType.FILEPATH:
                document_as_markdown, image_data, page_count = self._perform_ocr_from_filepath(filepath=document)
            else:
                logger.error(f"Received input type '{input_type}' which is neither a URL nor a filepath.")
                continue

            if self._store:
                session_dir = self._storage.store_ocr_result(
                    source=document,
                    markdown_content=document_as_markdown,
                    model=self._model,
                    page_count=page_count,
                    image_data=image_data,
                )
                logger.info(f"Stored OCR result to: {session_dir}")

            if self._display:
                print(document_as_markdown)

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for the OCR API request.

        Returns:
            dict[str, str]: Headers dictionary containing authorization and content-type.

        Raises:
            ValueError: If the API key environment variable is not set.
        """
        api_key = environ.get(self._api_key)
        if not api_key:
            raise ValueError(f"API key environment variable '{self._api_key}' is not set.")
        return {
            "accept": "application/json",
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }

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
        self, headers: dict[str, str], content: dict[str, str | bool | dict[str, str | None]]
    ) -> Response | None:
        """Make an OCR API request, returning None on network or HTTP failure.

        Args:
            headers (dict[str, str]): HTTP headers for the request.
            content (dict): JSON payload for the OCR API.

        Returns:
            Response | None: The Response object if successful, None if the request failed.
        """
        try:
            response = post(url=self._ocr_endpoint, headers=headers, json=content, timeout=30)
            return response if response.ok else None
        except RequestException:
            return None

    def _parse_ocr_response(self, response: Response) -> tuple[str, list[tuple[str, bytes]], int]:
        """Parse the OCR API response and extract markdown content and images.

        Args:
            response (Response): The HTTP response from the OCR API.

        Returns:
            tuple[str, list[tuple[str, bytes]], int]: A tuple containing:
                - The document content as markdown string.
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
            markdown_parts.append(f"\n\n### Page {page_index}\n{page_markdown}")
            for image in page["images"]:
                image_bytes = base64.b64decode(image["image_base64"].split(",", maxsplit=1)[1])
                image_data_list.append((image["id"], image_bytes))

        document_as_markdown = "".join(markdown_parts)
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
            "include_image_base64": True,
        }

        content_img: dict[str, str | bool | dict[str, str | None]] = {
            "model": self._model,
            "document": {
                "type": "image_url",
                "image_url": url,
            },
        }

        response = self._make_ocr_request(headers, content_pdf)
        if response is None:
            logger.warning("Document request failed, trying as image.")
            response = self._make_ocr_request(headers, content_img)

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
            "include_image_base64": True,
        }

        response = self._make_ocr_request(headers, content_pdf_local)
        if response is None:
            raise RuntimeError(f"OCR request failed for file: {filepath}")

        return self._parse_ocr_response(response)
