"""Holds all tests realting to storage.py."""

import pytest


class TestChat:
    """Holds all tests related to the Chat class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> None:
        pass

    class TestName:
        pass
