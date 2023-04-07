"""
Holds the tests for the install file
"""
import os
import shutil
from uuid import uuid4

import pytest

from src.main.install import Install


class TestInstall:
    @pytest.fixture(scope="session")
    def setup_teardown(self):
        random_id = "_".join(["test", str(uuid4()).split("-", 1)[0]])
        install = Install(openai_api_key="invalid_key", random_id=random_id)
        install.create_folders()

        yield install

        shutil.rmtree(install.gptcli_filepath, ignore_errors=True)

    @pytest.fixture(scope="session")
    def setup_teardown_no_folders(self):
        random_id = "_".join(["test", str(uuid4()).split("-", 1)[0]])
        install = Install(random_id=random_id)

        return install

    def test_should_detect_the_gptcli_folder_is_missing(self, setup_teardown_no_folders):
        install = setup_teardown_no_folders
        is_present = install.is_gptcli_folder_present()

        assert not is_present, "gtpcli folder found"

    def test_should_detect_the_keys_folder_is_missing(self, setup_teardown_no_folders):
        install = setup_teardown_no_folders
        is_present = install.is_keys_folder_present()

        assert not is_present, "keys folder found"

    def test_should_detect_the_openai_file_is_missing(self, setup_teardown_no_folders):
        install = setup_teardown_no_folders
        is_present = install.is_openai_file_present()

        assert not is_present, "openai file found"

    def test_should_detect_gptcli_folder_is_present(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_gptcli_folder_present()

        assert is_present, "gtpcli folder not found"

    def test_should_detect_the_keys_folder_is_present(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_keys_folder_present()

        assert is_present, "keys folder not found"

    def test_should_detect_the_openai_file_is_present(self, setup_teardown):
        install = setup_teardown
        is_present = install.is_openai_file_present()

        assert is_present, "openai folder not found"

    def test_should_detect_the_openai_file_contains_one_line(self, setup_teardown):
        install = setup_teardown
        install.load_api_key_to_openai_file()
        contains_one_line = install.openai_contains_one_line()

        assert contains_one_line, "openai file does not contain one line"

    def test_should_create_gptcli_folder_in_home_directory(self, setup_teardown):
        install = setup_teardown
        filepath = install.gptcli_filepath
        is_created = False
        is_created = os.path.exists(filepath)

        assert is_created, "gptcli was not created"

    def test_should_create_keys_folder_under_gptcli_folder(self, setup_teardown):
        install = setup_teardown
        filepath = install.keys_filepath
        is_created = False
        is_created = os.path.exists(filepath)

        assert is_created, "keys was not created"

    def test_should_create_openai_file_under_keys_folder(self, setup_teardown):
        install = setup_teardown
        filepath = install.openai_filepath
        is_created = False
        try:
            with open(filepath, "r", encoding="utf8"):
                pass
            is_created = True
        except FileNotFoundError:
            is_created = False

        assert is_created, "openai was not created"

    def test_should_load_openai_file_with_api_key(self, setup_teardown):
        install = setup_teardown
        install.load_api_key_to_openai_file()
        is_loaded = False
        with open(install.openai_filepath, "r", encoding="utf8") as filepointer:
            line = filepointer.readline()
            if len(line) > 0:
                is_loaded = True

        assert is_loaded, "failed to load openai file with API key"

    def test_should_load_openai_api_key_to_environment_variable(self, setup_teardown):
        install = setup_teardown
        install.load_api_key_to_environment_variable()
        key = os.getenv("OPENAI_API_KEY")
        is_loaded = key != None

        assert is_loaded, "failed to load environment variable with openai api key"
