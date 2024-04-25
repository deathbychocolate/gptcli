"""Allow ingestion of external textual infromation.
Such as text from the terminal, or a text file.
"""

import logging
import mimetypes
from abc import ABC, abstractmethod

import filetype
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class File(ABC):
    """Abstract class meant to represent all common files supported by GPTCLI."""

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath

    @abstractmethod
    def extract_text(self) -> str: ...


class Text(File):
    """Meant to ingest text from a file"""

    def __init__(self, filepath: str) -> None:
        super().__init__(filepath=filepath)

    def extract_text(self) -> str:
        """Allows for the user to select any file to ingest text from.
        Is intended only for plaintext format.

        Args:
            filepath (str): The filepath of the file we want to ingest.

        Returns:
            str: A string of text found in the file that of the filepath.
        """
        text = ""
        try:
            with open(self.filepath, "r", encoding="utf8") as filepointer:
                text = filepointer.read()
        except FileNotFoundError:
            logger.warning("File %s not found. Returning empty value.", self.filepath)

        return text

    @staticmethod
    def is_text(filepath: str) -> bool:
        """Check if the file is indeed a Text file.

        Returns:
            bool: True if it is a text file and False otherwise
        """
        mime_type, _ = mimetypes.guess_type(filepath)
        is_text = mime_type is not None and mime_type.split("/", maxsplit=2)[0] == "text"
        return is_text


class PDF(File):
    """Object meant to manage PDF files"""

    def __init__(self, filepath: str) -> None:
        super().__init__(filepath=filepath)

    def extract_text(self) -> str:
        """Allows for the user to select any file to ingest text from.
        Is intended only for PDF files.

        Returns:
            str: A string of text found in the file that of the filepath.
        """
        reader = PdfReader(self.filepath)
        text = " ".join([page.extract_text() for page in reader.pages])

        return text

    @staticmethod
    def is_pdf(filepath: str) -> bool:
        """Check if the file is indeed a PDF file.

        Returns:
            bool: True if it is a PDF | False if it is not a PDF | False if it is not supported
        """
        kind = filetype.guess(filepath)

        if kind is None:  # filetype not supported
            is_pdf = False
        elif kind.extension == "pdf" and kind.mime == "application/pdf":
            is_pdf = True
        else:
            is_pdf = False

        return is_pdf
