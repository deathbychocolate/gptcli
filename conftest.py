"""File to hold the config for all our tests."""

import pytest
from dotenv import find_dotenv, load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Load .env.tests for pytest run."""
    load_dotenv(find_dotenv(".env.tests"))
