"""Allow ingestion of external textual infromation.
Such as text from the terminal, or a text file.
"""

import logging

logger = logging.getLogger(__name__)


class TextFile:
    """Meant to ingest text from a file"""

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath

    def get_file_content(self) -> str:
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

    @property
    def filepath(self) -> str:
        return self._filepath
