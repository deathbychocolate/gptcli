"""Tests for the validators module."""

import os
from pathlib import Path

import pytest

from gptcli.src.common.validators import (
    InputType,
    classify_input,
    is_filepath,
    is_url,
)


class TestIsUrl:
    """Tests for the is_url function."""

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://example.com", id="https_basic"),
            pytest.param("https://example.com/path/to/resource", id="with_path"),
            pytest.param("https://example.com/search?q=hello", id="with_query"),
            pytest.param("http://192.168.1.1/api", id="ip_address"),
        ],
    )
    def test_valid_urls_return_true(self, url: str) -> None:
        assert is_url(url) is True

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param("", id="empty_string"),
            pytest.param("/path/to/file", id="filepath"),
            pytest.param("not a url", id="arbitrary_text"),
            pytest.param("example.com", id="missing_scheme"),
        ],
    )
    def test_invalid_inputs_return_false(self, value: str) -> None:
        assert is_url(value) is False

    def test_localhost_returns_false(self) -> None:
        """The validators library does not consider localhost as valid (no TLD)."""
        assert is_url("http://localhost:3000") is False


class TestIsFilepath:
    """Tests for the is_filepath function."""

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/home/user/file.txt", id="absolute_path"),
            pytest.param("/var/log/syslog", id="system_path"),
            pytest.param("/", id="root"),
        ],
    )
    def test_absolute_paths_return_true(self, path: str) -> None:
        assert is_filepath(path) is True

    def test_existing_relative_path_returns_true(self) -> None:
        original_cwd = os.getcwd()
        try:
            os.chdir(Path(__file__).parent)
            assert is_filepath("test_validators.py") is True
        finally:
            os.chdir(original_cwd)

    def test_nonexistent_relative_path_returns_false(self) -> None:
        assert is_filepath("nonexistent_file_xyz123.txt") is False

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://example.com", id="https"),
            pytest.param("http://example.com/path", id="http_with_path"),
        ],
    )
    def test_urls_return_false(self, url: str) -> None:
        assert is_filepath(url) is False

    def test_empty_string_returns_false(self) -> None:
        assert is_filepath("") is False


class TestClassifyInput:
    """Tests for the classify_input function."""

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://example.com", id="https"),
            pytest.param("https://api.example.com/v1/users?id=123", id="api_url"),
        ],
    )
    def test_urls_classified_as_url(self, url: str) -> None:
        assert classify_input(url) == InputType.URL

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/path/to/file", id="absolute_path"),
            pytest.param("example.com", id="domain_without_scheme"),
            pytest.param("arbitrary text", id="arbitrary_text"),
        ],
    )
    def test_non_urls_classified_as_filepath(self, path: str) -> None:
        assert classify_input(path) == InputType.FILEPATH


class TestInputType:
    """Tests for the InputType enum."""

    def test_enum_values(self) -> None:
        assert InputType.URL.value == "url"
        assert InputType.FILEPATH.value == "filepath"
