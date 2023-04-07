"""
Holds the tests for the machine file
"""
import os
import shutil
from uuid import uuid4

import pytest

from src.main.install import Install


class TestInstall:
    @pytest.fixture(scope="session")
    def setup_teardown(self):
        random_id = str(uuid4()).split("-", 1)[0]
        install = Install(random_id=random_id)
        install.create_folders()

        yield install

        shutil.rmtree(install.gptcli_filepath, ignore_errors=True)

    def test_should_detect_if_the_hidden_folder_gptcli_is_present_in_the_home_directory(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_gptcli_folder_present()
        assert is_present, "Hidden folder gtpcli not found in home dir"

    def test_should_detect_if_the_keys_folder_is_present_under_the_gptcli_folder(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_keys_folder_present()
        assert is_present, "keys folder not found in .gptcli"

    def test_should_detect_if_the_openai_file_is_present_under_the_keys_folder(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_openai_file_present()
        assert is_present, "openai file not found in keys folder"

    def test_should_detect_if_the_openai_file_contains_one_line(self, setup_teardown):
        install = setup_teardown
        contains_one_line = install.openai_contains_one_line()
        assert contains_one_line, "openai file does not contain one line"

    def test_should_detect_if_the_openai_file_is_populated_with_a_valid_api_key(self, setup_teardown):
        # TODO break up the test, it seems to require too much to check this, design better
        install = setup_teardown
        is_valid_api_key = install.is_openai_file_populated_with_a_valid_api_key()
        assert is_valid_api_key, "openai file does not contain a valid API key"

    def test_should_create_gptcli_folder_in_home_directory(self, setup_teardown):
        install = setup_teardown
        assert False

    def test_should_create_keys_folder_under_gptcli_folder(self, setup_teardown):
        install = setup_teardown
        assert False

    def test_should_create_openai_file_under_keys_folder(self, setup_teardown):
        install = setup_teardown
        assert False
