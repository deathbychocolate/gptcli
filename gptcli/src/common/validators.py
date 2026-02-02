"""Validation utilities for classifying input as URLs or filepaths."""

from enum import Enum
from os import path

import validators


class InputType(Enum):
    """Enum representing the type of input: URL or filepath."""

    URL = "url"
    FILEPATH = "filepath"
    UNSUPPORTED = "unsupported"


def is_url(document: str) -> bool:
    """Check if the given document is a valid URL.

    Args:
        document (str): The string to validate.

    Returns:
        bool: True if the document is a valid URL, False otherwise.
    """
    return validators.url(document) is True


def is_filepath(document: str) -> bool:
    """Check if the given document is a valid filepath that exists.

    Args:
        document (str): The string to validate.

    Returns:
        bool: True if the document is an existing filepath, False otherwise.
    """
    if is_url(document):
        return False
    return path.exists(document)


def classify_input(document: str) -> InputType:
    """Classify input as URL, FILEPATH, or UNSUPPORTED.

    Args:
        document (str): The string to classify.

    Returns:
        InputType: The classified input type (URL, FILEPATH, or UNSUPPORTED).
    """
    if is_url(document=document):
        return InputType.URL
    elif is_filepath(document=document):
        return InputType.FILEPATH
    else:
        return InputType.UNSUPPORTED
