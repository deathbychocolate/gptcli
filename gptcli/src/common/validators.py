"""Validation utilities for classifying input as URLs or filepaths."""

from enum import Enum
from os import path

import validators


class InputType(Enum):
    """Enum representing the type of input: URL or filepath."""

    URL = "url"
    FILEPATH = "filepath"


def is_url(document: str) -> bool:
    """Check if the given document is a valid URL.

    Args:
        document (str): The string to validate.

    Returns:
        bool: True if the document is a valid URL, False otherwise.
    """
    return validators.url(document) is True


def is_filepath(document: str) -> bool:
    """Check if the given document is a valid filepath (not a URL).

    Args:
        document (str): The string to validate.

    Returns:
        bool: True if the document is a filepath, False otherwise.
    """
    if is_url(document):
        return False
    return path.isabs(document) or path.exists(document)


def classify_input(document: str) -> InputType:
    """Classify input as URL or FILEPATH.

    Args:
        document (str): The string to classify.

    Returns:
        InputType: InputType.URL if the document is a valid URL, InputType.FILEPATH otherwise.
    """
    return InputType.URL if is_url(document) else InputType.FILEPATH
