"""File to hold all decorators relevant to the project."""

import logging
import sys
from logging import Logger
from typing import Any, Callable

logger: Logger = logging.getLogger(__name__)


def user_triggered_abort(function: Callable[..., Any]) -> Callable[..., Any]:
    """Use this wrapper to catch KeyboardInterrupt or EOFError errors.

    This is useful if for example the user decides to use Ctrl+C to
    exit the program entirely.

    Args:
        function (Callable[..., Any]): The method or function to wrap around.
    """

    def decorator(*args: Any, **kwargs: Any) -> Any:
        logger.info("Calling '%s', with args '%s', and kwargs '%s'", function.__qualname__, args, kwargs)
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt as exception:
            print()  # add new line
            logger.info("'KeyboardInterrupt' detected, exiting program.")
            logger.exception(exception)
            sys.exit()
        except EOFError as exception:
            print()  # add new line
            logger.info("'EOFError' detected, exiting program.")
            logger.exception(exception)
            sys.exit()

    return decorator


def allow_graceful_stream_exit(function: Callable[..., Any]) -> Callable[..., Any]:
    """Use this wrapper to catch KeyboardInterrupt or EOFError errors.

    This is useful if for example the user decides to use Ctrl+C to
    exit the printing of text when using streaming mode.

    Args:
        function (Callable[..., Any]): The method or function to wrap around.
    """

    def decorator(*args: Any, **kwargs: Any) -> Any:
        logger.info("Calling '%s', with args '%s', and kwargs '%s'", function.__qualname__, args, kwargs)
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt as exception:
            print()  # add new line
            logger.info("'KeyboardInterrupt' detected, exiting chat.")
            logger.exception(exception)
        except EOFError as exception:
            print()  # add new line
            logger.info("'EOFError' detected, exiting chat.")
            logger.exception(exception)

    return decorator
