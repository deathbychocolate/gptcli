"""File to centralize HTTP errors"""

from enum import Enum


class HttpClientErrorCodes(Enum):
    """Will contain error codes as defined by Mozilla"""

    UNAUTHORIZED = 401
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429


class HttpClientErrorDescriptions(Enum):
    """Will contain error descriptions as defined by Mozilla"""

    # pylint: disable=line-too-long
    UNAUTHORIZED = "The client must authenticate itself to get the requested response."
    NOT_FOUND = "The server cannot find the requested resource."
    TOO_MANY_REQUESTS = "The user has sent too many requests in a given amount of time."


class HttpServerErrorCodes(Enum):
    """Will contain error codes as defined by Mozilla"""

    SERVICE_UNAVAILABLE = 503


class HttpServerErrorDescriptions(Enum):
    """Will contain error descriptions as defined by Mozilla"""

    # pylint: disable=line-too-long
    SERVICE_UNAVAILABLE = "The server is not ready to handle the request. Common causes are a server that is down for maintenance or that is overloaded."
