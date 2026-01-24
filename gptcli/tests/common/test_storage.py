"""Holds all the tests for storage.py."""

import json
import os
import re
from typing import Any, Generator
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from gptcli.src.common.constants import MistralModelsOcr, ProviderNames
from gptcli.src.common.storage import Storage, StorageEmpty


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

    class TestCreateOcrSessionDir:

        @pytest.fixture(scope="session", params=ProviderNames.to_list())
        def storage_instance(self, request: SubRequest) -> Generator[Storage, None, None]:
            storage: Storage = Storage(provider=request.param)
            yield storage

        def test_should_return_a_string(self, storage_instance: Storage) -> None:
            session_dir: str = storage_instance._create_ocr_session_dir()
            assert isinstance(session_dir, str)

        def test_should_end_with_double_underscore_ocr_suffix(self, storage_instance: Storage) -> None:
            session_dir: str = storage_instance._create_ocr_session_dir()
            assert session_dir.endswith("__ocr")

        def test_should_match_epoch_date_time_ocr_naming_pattern(self, storage_instance: Storage) -> None:
            session_dir: str = storage_instance._create_ocr_session_dir()
            folder_name: str = session_dir.split("/")[-1]
            pattern = r"^\d+__\d{4}_\d{2}_\d{2}__\d{2}_\d{2}_\d{2}__ocr$"
            assert re.match(pattern, folder_name), f"'{folder_name}' does not match pattern"

        def test_should_be_inside_provider_ocr_storage_directory(self, storage_instance: Storage) -> None:
            session_dir: str = storage_instance._create_ocr_session_dir()
            assert "/storage/ocr/" in session_dir

        def test_consecutive_calls_should_all_produce_valid_ocr_paths(self, storage_instance: Storage) -> None:
            paths: set[str] = set()
            for _ in range(5):
                paths.add(storage_instance._create_ocr_session_dir())
            for p in paths:
                assert p.endswith("__ocr")

    class TestExtractFilenameFromSource:

        URL: str = "https://example.com"

        # Filepath cases

        def test_simple_filepath(self) -> None:
            assert Storage._extract_filename_from_source("/path/to/document.pdf") == "document.pdf"

        def test_filepath_with_nested_directories(self) -> None:
            assert Storage._extract_filename_from_source("/a/b/c/d/file.txt") == "file.txt"

        def test_filepath_with_spaces(self) -> None:
            assert Storage._extract_filename_from_source("/path/to/my file.pdf") == "my file.pdf"

        def test_filepath_with_no_extension(self) -> None:
            assert Storage._extract_filename_from_source("/path/to/noextension") == "noextension"

        def test_filepath_root_file(self) -> None:
            assert Storage._extract_filename_from_source("/file.pdf") == "file.pdf"

        def test_filepath_hidden_file(self) -> None:
            assert Storage._extract_filename_from_source("/path/to/.hidden") == ".hidden"

        # URL cases

        def test_simple_url(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/files/doc.pdf") == "doc.pdf"

        def test_url_with_query_params(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/doc.pdf?token=abc") == "doc.pdf"

        def test_url_with_fragment(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/doc.pdf#page=1") == "doc.pdf"

        def test_url_with_percent_encoded_spaces(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/my%20doc.pdf") == "my doc.pdf"

        def test_url_with_percent_encoded_unicode(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/%E6%96%87%E6%A1%A3.pdf") == "文档.pdf"

        def test_url_with_trailing_slash_returns_empty(self) -> None:
            assert Storage._extract_filename_from_source(f"{self.URL}/") == ""

        def test_url_with_no_path_returns_empty(self) -> None:
            assert Storage._extract_filename_from_source(self.URL) == ""

    class TestDeriveMarkdownFilenameFromSource:

        URL: str = "https://example.com"

        # Filepath cases

        def test_simple_pdf_filepath(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/document.pdf") == "document.md"

        def test_filepath_with_multiple_dots_replaces_only_last_extension(self) -> None:
            assert (
                Storage.derive_markdown_filename_from_source("/path/to/file.name.with.dots.pdf")
                == "file.name.with.dots.md"
            )

        def test_filepath_with_no_extension_appends_md(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/noextension") == "noextension.md"

        def test_filepath_with_spaces(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/my document.pdf") == "my document.md"

        def test_filepath_with_unicode_characters(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/文档.pdf") == "文档.md"
            assert Storage.derive_markdown_filename_from_source("/path/to/документ.pdf") == "документ.md"

        def test_filepath_with_special_characters(self) -> None:
            assert (
                Storage.derive_markdown_filename_from_source("/path/to/file-name_v2 (1).pdf") == "file-name_v2 (1).md"
            )

        def test_filepath_hidden_file(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/.hidden") == ".hidden.md"

        def test_filepath_with_uppercase_extension(self) -> None:
            assert Storage.derive_markdown_filename_from_source("/path/to/DOCUMENT.PDF") == "DOCUMENT.md"

        # URL cases

        def test_simple_url(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/files/document.pdf") == "document.md"

        def test_url_with_query_parameters(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/file.pdf?token=abc") == "file.md"

        def test_url_with_fragment(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/file.pdf#page=5") == "file.md"

        def test_url_with_query_and_fragment(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/file.pdf?v=1#section") == "file.md"

        def test_url_with_percent_encoded_spaces(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/my%20document.pdf") == "my document.md"

        def test_url_with_percent_encoded_unicode(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/%E6%96%87%E6%A1%A3.pdf") == "文档.md"

        def test_url_with_trailing_slash_uses_fallback(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/") == "document.md"

        def test_url_with_no_path_uses_fallback(self) -> None:
            assert Storage.derive_markdown_filename_from_source(self.URL) == "document.md"

        def test_url_with_only_query_params_uses_fallback(self) -> None:
            assert Storage.derive_markdown_filename_from_source(f"{self.URL}/?id=123") == "document.md"

        def test_url_with_deep_path(self) -> None:
            assert Storage.derive_markdown_filename_from_source("https://a.com/b/c/d/e/f/doc.pdf") == "doc.md"

        # Error cases

        def test_empty_string_raises_value_error(self) -> None:
            with pytest.raises(ValueError):
                Storage.derive_markdown_filename_from_source("")

        def test_whitespace_only_raises_value_error(self) -> None:
            with pytest.raises(ValueError):
                Storage.derive_markdown_filename_from_source("   ")

    class TestBuildOcrMetadata:

        URL: str = "https://example.com"

        @pytest.fixture
        def storage(self) -> Storage:
            return Storage(provider=ProviderNames.MISTRAL.value)

        # Structure and type validation

        def test_returns_dict(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert isinstance(result, dict)

        def test_contains_source_section(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert "source" in result
            assert isinstance(result["source"], dict)

        def test_contains_ocr_section(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert "ocr" in result
            assert isinstance(result["ocr"], dict)

        def test_contains_output_section(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert "output" in result
            assert isinstance(result["output"], dict)

        # Source section

        def test_source_input_matches_provided_source(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["source"]["input"] == "/path/to/doc.pdf"

        def test_source_input_type_is_filepath_for_local_path(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["source"]["input_type"] == "filepath"

        def test_source_input_type_is_url_for_http_url(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source=f"{self.URL}/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["source"]["input_type"] == "url"

        def test_source_filename_extracted_from_filepath(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/document.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="document.md",
                images=[],
            )
            assert result["source"]["filename"] == "document.pdf"

        def test_source_filename_extracted_from_url(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source=f"{self.URL}/files/report.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="report.md",
                images=[],
            )
            assert result["source"]["filename"] == "report.pdf"

        def test_source_filename_with_unicode(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/文档.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="文档.md",
                images=[],
            )
            assert result["source"]["filename"] == "文档.pdf"

        # OCR section

        def test_ocr_created_is_float(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert isinstance(result["ocr"]["created"], float)

        def test_ocr_uuid_is_valid_format(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            assert re.match(uuid_pattern, result["ocr"]["uuid"])

        def test_ocr_model_matches_provided_model(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["ocr"]["model"] == MistralModelsOcr.MISTRAL_OCR.value

        def test_ocr_provider_matches_storage_provider(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["ocr"]["provider"] == ProviderNames.MISTRAL.value

        def test_ocr_page_count_matches_provided_count(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=5,
                markdown_file="doc.md",
                images=[],
            )
            assert result["ocr"]["page_count"] == 5

        # Output section

        def test_output_markdown_file_matches_provided_value(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["output"]["markdown_file"] == "doc.md"

        def test_output_images_empty_list(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["output"]["images"] == []

        def test_output_images_with_multiple_files(self, storage: Storage) -> None:
            images = ["page_1_img_0.png", "page_1_img_1.jpg", "page_2_img_0.png"]
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=2,
                markdown_file="doc.md",
                images=images,
            )
            assert result["output"]["images"] == images

        # Edge cases

        def test_url_with_query_params_extracts_filename_correctly(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source=f"{self.URL}/doc.pdf?token=abc123",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
            )
            assert result["source"]["filename"] == "doc.pdf"

        def test_consecutive_calls_produce_different_uuids(self, storage: Storage) -> None:
            uuids: set[str] = set()
            for _ in range(5):
                result = storage._build_ocr_metadata(
                    source="/path/to/doc.pdf",
                    model=MistralModelsOcr.MISTRAL_OCR.value,
                    page_count=1,
                    markdown_file="doc.md",
                    images=[],
                )
                uuids.add(result["ocr"]["uuid"])
            assert len(uuids) == 5

    class TestStoreOcrResult:

        URL: str = "https://example.com"

        @pytest.fixture
        def storage_with_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._ocr_dir = str(tmp_path)
            return storage

        # Directory creation

        def test_creates_session_directory(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            assert len(subdirs) == 1
            assert subdirs[0].endswith("__ocr")

        def test_returns_session_directory_path(self, storage_with_tmp_dir: Storage) -> None:
            result = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert result.endswith("__ocr")
            assert os.path.isdir(result)

        # Markdown file

        def test_creates_markdown_file_with_derived_name(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/document.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert os.path.exists(os.path.join(session_dir, "document.md"))

        def test_markdown_file_contains_correct_content(self, storage_with_tmp_dir: Storage) -> None:
            markdown_content = "# Title\n\nSome content here."
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content=markdown_content,
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            with open(os.path.join(session_dir, "doc.md"), "r", encoding="utf8") as f:
                assert f.read() == markdown_content

        def test_markdown_file_handles_unicode_content(self, storage_with_tmp_dir: Storage) -> None:
            markdown_content = "# 文档标题\n\n这是中文内容。\n\nКириллица тоже работает."
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/文档.pdf",
                markdown_content=markdown_content,
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            with open(os.path.join(session_dir, "文档.md"), "r", encoding="utf8") as f:
                assert f.read() == markdown_content

        def test_markdown_file_handles_empty_content(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=0,
                image_data=[],
            )
            with open(os.path.join(session_dir, "doc.md"), "r", encoding="utf8") as f:
                assert f.read() == ""

        # Metadata file

        def test_creates_metadata_json_file(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert os.path.exists(os.path.join(session_dir, "metadata.json"))

        def test_metadata_json_is_valid_json(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            with open(os.path.join(session_dir, "metadata.json"), "r", encoding="utf8") as f:
                metadata = json.load(f)
            assert isinstance(metadata, dict)

        def test_metadata_json_contains_correct_source(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/document.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=3,
                image_data=[("img1.png", b"fake"), ("img2.png", b"fake")],
            )
            with open(os.path.join(session_dir, "metadata.json"), "r", encoding="utf8") as f:
                metadata = json.load(f)
            assert metadata["source"]["input"] == "/path/to/document.pdf"
            assert metadata["source"]["filename"] == "document.pdf"

        def test_metadata_json_contains_correct_ocr_info(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=5,
                image_data=[],
            )
            with open(os.path.join(session_dir, "metadata.json"), "r", encoding="utf8") as f:
                metadata = json.load(f)
            assert metadata["ocr"]["model"] == MistralModelsOcr.MISTRAL_OCR.value
            assert metadata["ocr"]["provider"] == ProviderNames.MISTRAL.value
            assert metadata["ocr"]["page_count"] == 5

        def test_metadata_json_contains_correct_output_info(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/report.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[("page_1_img_0.png", b"fake"), ("page_1_img_1.jpg", b"fake")],
            )
            with open(os.path.join(session_dir, "metadata.json"), "r", encoding="utf8") as f:
                metadata = json.load(f)
            assert metadata["output"]["markdown_file"] == "report.md"
            assert metadata["output"]["images"] == ["page_1_img_0.png", "page_1_img_1.jpg"]

        # Image saving

        def test_saves_image_files_to_session_directory(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[("img1.png", b"PNG image data"), ("img2.jpg", b"JPEG image data")],
            )
            assert os.path.exists(os.path.join(session_dir, "img1.png"))
            assert os.path.exists(os.path.join(session_dir, "img2.jpg"))

        def test_saved_image_contains_correct_data(self, storage_with_tmp_dir: Storage) -> None:
            image_bytes = b"This is test image data"
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[("test_image.png", image_bytes)],
            )
            with open(os.path.join(session_dir, "test_image.png"), "rb") as f:
                assert f.read() == image_bytes

        # URL source edge cases

        def test_url_source_extracts_filename_for_markdown(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source=f"{self.URL}/files/report.pdf?token=abc",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert os.path.exists(os.path.join(session_dir, "report.md"))

        def test_url_source_uses_fallback_filename_when_no_path(self, storage_with_tmp_dir: Storage) -> None:
            session_dir = storage_with_tmp_dir.store_ocr_result(
                source=f"{self.URL}/",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert os.path.exists(os.path.join(session_dir, "document.md"))

    class TestExtractMessages:

        @pytest.fixture
        def storage_with_empty_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._json_dir = str(tmp_path)
            return storage

        def test_prints_storage_empty_warning_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            with pytest.raises(StorageEmpty) as exc_info:
                storage_with_empty_tmp_dir.extract_messages()
            assert "No chat sessions found" in str(exc_info.value)

    class TestExtractFormatAndShowMessagesForDisplay:

        URL: str = "https://example.com"

        @pytest.fixture
        def storage_with_empty_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._json_dir = str(tmp_path)
            return storage

        def test_returns_none_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            result = storage_with_empty_tmp_dir.extract_and_show_messages_for_display()  # type: ignore[func-returns-value]
            assert result is None

        def test_prints_warning_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            with patch("gptcli.src.common.storage.print_formatted_text") as mock_print:
                storage_with_empty_tmp_dir.extract_and_show_messages_for_display()
                mock_print.assert_called_once()
                call_args = str(mock_print.call_args)
                assert "No chats found in storage" in call_args

        def test_returns_none(self, storage_with_empty_tmp_dir: Storage, tmp_path: str) -> None:
            chat_data: dict[str, list[Any]] = {"messages": []}
            chat_file = os.path.join(tmp_path, "123__2024_01_01__12_00_00__chat.json")
            with open(chat_file, "w", encoding="utf8") as f:
                json.dump(chat_data, f)

            result = storage_with_empty_tmp_dir.extract_and_show_messages_for_display()  # type: ignore[func-returns-value]
            assert result is None

        def test_does_not_raise_for_empty_messages(self, storage_with_empty_tmp_dir: Storage, tmp_path: str) -> None:
            chat_data: dict[str, list[Any]] = {"messages": []}
            chat_file = os.path.join(tmp_path, "123__2024_01_01__12_00_00__chat.json")
            with open(chat_file, "w", encoding="utf8") as f:
                json.dump(chat_data, f)

            # Should not raise any exception
            storage_with_empty_tmp_dir.extract_and_show_messages_for_display()
