"""Holds all the tests for storage.py."""

from typing import Generator

import pytest
from _pytest.fixtures import SubRequest

from gptcli.src.common.constants import ProviderNames
from gptcli.src.common.storage import Storage


class TestStorage:

    class TestCreateJsonFilepath:

        @pytest.fixture(scope="session", params=ProviderNames.to_list())
        def setup_teardown(self, request: SubRequest) -> Generator[str, None, None]:
            """Create a filepath to test for the provider OpenAI."""
            storage: Storage = Storage(provider=request.param)
            filepath: str = storage._create_json_filepath()
            yield filepath

        def test_should_return_a_string(self, setup_teardown: str) -> None:
            filepath: str = setup_teardown
            assert isinstance(filepath, str)

        def test_should_return_a_string_with_a_json_file_extension(self, setup_teardown: str) -> None:
            filepath: str = setup_teardown
            assert filepath.endswith(".json")
