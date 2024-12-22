"""File to hold all decorators relevant to the project."""

import logging
import sys
from logging import Logger

logger: Logger = logging.getLogger(__name__)


def user_triggered_abort(function):

    def decorator(*args, **kwargs):
        logger.info("Calling '%s', with args '%s', and kwargs '%s'", function.__qualname__, args, kwargs)
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt as exception:
            print()
            logger.info("'KeyboardInterrupt' detected, exiting program.")
            logger.exception(exception)
            sys.exit()
        except EOFError as exception:
            print()
            logger.info("'EOFError' detected, exiting program.")
            logger.exception(exception)
            sys.exit()

    return decorator


def allow_graceful_stream_exit(function):

    def decorator(*args, **kwargs):
        logger.info("Calling '%s', with args '%s', and kwargs '%s'", function.__qualname__, args, kwargs)
        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt as exception:
            print()
            logger.info("'KeyboardInterrupt' detected, exiting chat.")
            logger.exception(exception)
        except EOFError as exception:
            print()
            logger.info("'EOFError' detected, exiting chat.")
            logger.exception(exception)

    return decorator
