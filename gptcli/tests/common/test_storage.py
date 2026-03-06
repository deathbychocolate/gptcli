"""Holds all the tests for storage.py."""

import json
import os
import re
import uuid
from typing import Any
from unittest.mock import patch

import pytest

from gptcli.constants import GPTCLI_MANIFEST_FILENAME as _MANIFEST_FILENAME
from gptcli.src.common.constants import MistralModelsOcr, ProviderNames
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.message import MessageFactory, Messages
from gptcli.src.common.storage import Storage, StorageEmpty


class TestStorage:

    @pytest.fixture
    def storage_with_ocr_tmp_dir(self, tmp_path: str) -> Storage:
        """Create a Storage instance with OCR directory set to a temporary path."""
        storage = Storage(provider=ProviderNames.MISTRAL.value)
        storage._ocr_dir = str(tmp_path)
        return storage

    @staticmethod
    def _append_manifest_entry(tmp_path: str, session_uuid: str, created: float) -> None:
        """Append a session entry to the plaintext manifest in tmp_path."""
        manifest_path = os.path.join(tmp_path, _MANIFEST_FILENAME)
        entries: list[dict[str, Any]] = []
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf8") as f:
                entries = json.load(f)
        entries.append({"uuid": session_uuid, "created": created})
        with open(manifest_path, "w", encoding="utf8") as f:
            json.dump(entries, f)

    @staticmethod
    def _create_ocr_session_with_manifest(tmp_path: str, md_filename: str, md_content: str, created: float) -> str:
        """Create a test OCR session directory with a markdown file and manifest entry."""
        session_uuid = str(uuid.uuid4())
        session_dir = os.path.join(tmp_path, session_uuid)
        os.makedirs(session_dir)
        with open(os.path.join(session_dir, md_filename), "w", encoding="utf8") as f:
            f.write(md_content)
        TestStorage._append_manifest_entry(tmp_path, session_uuid, created)
        return session_dir

    class TestCreateSessionDir:

        @pytest.fixture
        def storage_instance(self, tmp_path: str) -> Storage:
            """Create a Storage instance with dirs pointing to tmp_path."""
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._chat_dir = os.path.join(str(tmp_path), "chat")
            storage._ocr_dir = os.path.join(str(tmp_path), "ocr")
            os.makedirs(storage._chat_dir)
            os.makedirs(storage._ocr_dir)
            return storage

        def test_should_return_a_tuple_of_three(self, storage_instance: Storage) -> None:
            result = storage_instance._create_session_dir(storage_instance._chat_dir)
            assert isinstance(result, tuple)
            assert len(result) == 3

        def test_session_dir_contains_uuid(self, storage_instance: Storage) -> None:
            session_dir, session_uuid, _ = storage_instance._create_session_dir(storage_instance._chat_dir)
            assert session_uuid in session_dir
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            assert re.match(uuid_pattern, session_uuid)

        def test_session_dir_is_inside_base_directory(self, storage_instance: Storage) -> None:
            session_dir, _, _ = storage_instance._create_session_dir(storage_instance._chat_dir)
            assert session_dir.startswith(storage_instance._chat_dir)

        def test_created_is_a_float(self, storage_instance: Storage) -> None:
            _, _, created = storage_instance._create_session_dir(storage_instance._chat_dir)
            assert isinstance(created, float)

        def test_consecutive_calls_produce_unique_uuids(self, storage_instance: Storage) -> None:
            uuids: set[str] = set()
            for _ in range(5):
                _, session_uuid, _ = storage_instance._create_session_dir(storage_instance._chat_dir)
                uuids.add(session_uuid)
            assert len(uuids) == 5

    class TestExtractFilenameFromSource:

        URL: str = "https://example.com"

        # Filepath cases

        def test_simple_filepath(self) -> None:
            assert Storage.extract_filename_from_source("/path/to/document.pdf") == "document.pdf"

        def test_filepath_with_nested_directories(self) -> None:
            assert Storage.extract_filename_from_source("/a/b/c/d/file.txt") == "file.txt"

        def test_filepath_with_spaces(self) -> None:
            assert Storage.extract_filename_from_source("/path/to/my file.pdf") == "my file.pdf"

        def test_filepath_with_no_extension(self) -> None:
            assert Storage.extract_filename_from_source("/path/to/noextension") == "noextension"

        def test_filepath_root_file(self) -> None:
            assert Storage.extract_filename_from_source("/file.pdf") == "file.pdf"

        def test_filepath_hidden_file(self) -> None:
            assert Storage.extract_filename_from_source("/path/to/.hidden") == ".hidden"

        # URL cases

        def test_simple_url(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/files/doc.pdf") == "doc.pdf"

        def test_url_with_query_params(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/doc.pdf?token=abc") == "doc.pdf"

        def test_url_with_fragment(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/doc.pdf#page=1") == "doc.pdf"

        def test_url_with_percent_encoded_spaces(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/my%20doc.pdf") == "my doc.pdf"

        def test_url_with_percent_encoded_unicode(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/%E6%96%87%E6%A1%A3.pdf") == "文档.pdf"

        def test_url_with_trailing_slash_returns_empty(self) -> None:
            assert Storage.extract_filename_from_source(f"{self.URL}/") == ""

        def test_url_with_no_path_returns_empty(self) -> None:
            assert Storage.extract_filename_from_source(self.URL) == ""

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

        def test_metadata_captures_source_information(self, storage: Storage) -> None:
            result = storage._build_ocr_metadata(
                source="/path/to/document.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="document.md",
                images=[],
                session_uuid="test-uuid",
                created=1704067200.0,
            )
            assert result["source"]["input"] == "/path/to/document.pdf"
            assert result["source"]["input_type"] == "filepath"
            assert result["source"]["filename"] == "document.pdf"

            url_result = storage._build_ocr_metadata(
                source=f"{self.URL}/files/report.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="report.md",
                images=[],
                session_uuid="test-uuid-2",
                created=1704067200.0,
            )
            assert url_result["source"]["input_type"] == "url"
            assert url_result["source"]["filename"] == "report.pdf"

        def test_metadata_captures_processing_details(self, storage: Storage) -> None:
            test_uuid = str(uuid.uuid4())
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=5,
                markdown_file="doc.md",
                images=[],
                session_uuid=test_uuid,
                created=1704067200.0,
            )
            assert isinstance(result["ocr"]["created"], float)
            assert result["ocr"]["uuid"] == test_uuid
            assert result["ocr"]["model"] == MistralModelsOcr.MISTRAL_OCR.value
            assert result["ocr"]["provider"] == ProviderNames.MISTRAL.value
            assert result["ocr"]["page_count"] == 5

        def test_metadata_captures_output_references(self, storage: Storage) -> None:
            images = ["page_1_img_0.png", "page_1_img_1.jpg", "page_2_img_0.png"]
            result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=2,
                markdown_file="doc.md",
                images=images,
                session_uuid="test-uuid",
                created=1704067200.0,
            )
            assert result["output"]["markdown_file"] == "doc.md"
            assert result["output"]["images"] == images

            empty_result = storage._build_ocr_metadata(
                source="/path/to/doc.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
                session_uuid="test-uuid",
                created=1704067200.0,
            )
            assert empty_result["output"]["images"] == []

        def test_handles_unicode_filenames_and_url_query_params(self, storage: Storage) -> None:
            unicode_result = storage._build_ocr_metadata(
                source="/path/to/文档.pdf",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="文档.md",
                images=[],
                session_uuid="test-uuid",
                created=1704067200.0,
            )
            assert unicode_result["source"]["filename"] == "文档.pdf"

            url_result = storage._build_ocr_metadata(
                source=f"{self.URL}/doc.pdf?token=abc123",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                markdown_file="doc.md",
                images=[],
                session_uuid="test-uuid",
                created=1704067200.0,
            )
            assert url_result["source"]["filename"] == "doc.pdf"

    class TestStoreOcrResult:

        URL: str = "https://example.com"

        @pytest.fixture
        def storage_with_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._ocr_dir = str(tmp_path)
            return storage

        # Directory creation

        def test_creates_uuid_session_directory(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            assert len(subdirs) == 1
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            assert re.match(uuid_pattern, subdirs[0])

        def test_returns_session_directory_path(self, storage_with_tmp_dir: Storage) -> None:
            result = storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            assert os.path.isdir(result)

        def test_creates_manifest(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            storage_with_tmp_dir.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            manifest_path = os.path.join(str(tmp_path), _MANIFEST_FILENAME)
            assert os.path.exists(manifest_path)
            with open(manifest_path, "r", encoding="utf8") as f:
                entries = json.load(f)
            assert len(entries) == 1
            assert "uuid" in entries[0]
            assert "created" in entries[0]

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

    class TestStoreMessages:

        @pytest.fixture
        def storage_with_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._chat_dir = str(tmp_path)
            return storage

        @staticmethod
        def _create_messages() -> Messages:
            factory = MessageFactory(provider=ProviderNames.MISTRAL.value)
            messages = Messages()
            msg = factory.user_message(role="user", content="Hello!", model="mistral-large-latest")
            messages.add(msg)
            return messages

        def test_creates_uuid_session_directory(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_tmp_dir.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            assert len(subdirs) == 1
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            assert re.match(uuid_pattern, subdirs[0])

        def test_creates_session_json(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_tmp_dir.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            assert os.path.exists(os.path.join(session_dir, "session.json"))

        def test_creates_metadata_json(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_tmp_dir.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            assert os.path.exists(os.path.join(session_dir, "metadata.json"))

        def test_creates_manifest(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_tmp_dir.store_messages(messages)
            manifest_path = os.path.join(str(tmp_path), _MANIFEST_FILENAME)
            assert os.path.exists(manifest_path)
            with open(manifest_path, "r", encoding="utf8") as f:
                entries = json.load(f)
            assert len(entries) == 1

        def test_metadata_contains_chat_section(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_tmp_dir.store_messages(messages, model="mistral-large-latest")
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            with open(os.path.join(session_dir, "metadata.json"), "r", encoding="utf8") as f:
                metadata = json.load(f)
            assert "chat" in metadata
            assert metadata["chat"]["model"] == "mistral-large-latest"
            assert metadata["chat"]["provider"] == ProviderNames.MISTRAL.value
            assert "uuid" in metadata["chat"]
            assert "created" in metadata["chat"]

        def test_does_not_store_empty_messages(self, storage_with_tmp_dir: Storage, tmp_path: str) -> None:
            messages = Messages()
            storage_with_tmp_dir.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            assert len(subdirs) == 0

    class TestExtractMessages:

        @pytest.fixture
        def storage_with_empty_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._chat_dir = str(tmp_path)
            return storage

        @staticmethod
        def _create_chat_session(tmp_path: str, content: str, created: float) -> str:
            """Create a test chat session with UUID directory, session.json, and manifest entry."""
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(tmp_path, session_uuid)
            os.makedirs(session_dir)
            chat_data: dict[str, list[dict[str, Any]]] = {
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                        "model": "mistral-large-latest",
                        "provider": "mistral",
                        "is_reply": False,
                        "created": 1704067200.0,
                        "uuid": "00000000-0000-0000-0000-000000000000",
                        "tokens": 5,
                    }
                ]
            }
            filepath = os.path.join(session_dir, "session.json")
            with open(filepath, "w", encoding="utf8") as f:
                json.dump(chat_data, f)
            TestStorage._append_manifest_entry(tmp_path, session_uuid, created)
            return session_dir

        def test_raises_storage_empty_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            with pytest.raises(StorageEmpty) as exc_info:
                storage_with_empty_tmp_dir.extract_messages()
            assert "No chat sessions found" in str(exc_info.value)

        def test_selects_newest_by_created_timestamp(self, storage_with_empty_tmp_dir: Storage, tmp_path: str) -> None:
            self._create_chat_session(str(tmp_path), "Old message", created=100.0)
            self._create_chat_session(str(tmp_path), "New message", created=200.0)
            messages = storage_with_empty_tmp_dir.extract_messages()
            assert messages is not None
            first_message = next(iter(messages))
            assert first_message.content == "New message"

    class TestDisplayLastChat:

        @pytest.fixture
        def storage_with_empty_tmp_dir(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._chat_dir = str(tmp_path)
            return storage

        def test_returns_none_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            result = storage_with_empty_tmp_dir.display_last_chat()  # type: ignore[func-returns-value]
            assert result is None

        def test_prints_warning_when_no_files_exist(self, storage_with_empty_tmp_dir: Storage) -> None:
            with patch("gptcli.src.common.storage.print_formatted_text") as mock_print:
                storage_with_empty_tmp_dir.display_last_chat()
                mock_print.assert_called_once()
                call_args = str(mock_print.call_args)
                assert "No chats found in storage" in call_args

        def test_returns_none_for_empty_session(self, storage_with_empty_tmp_dir: Storage, tmp_path: str) -> None:
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(str(tmp_path), session_uuid)
            os.makedirs(session_dir)
            chat_data: dict[str, list[Any]] = {"messages": []}
            with open(os.path.join(session_dir, "session.json"), "w", encoding="utf8") as f:
                json.dump(chat_data, f)
            TestStorage._append_manifest_entry(str(tmp_path), session_uuid, 123.0)

            result = storage_with_empty_tmp_dir.display_last_chat()  # type: ignore[func-returns-value]
            assert result is None

    class TestExtractLastOcrResult:

        def test_returns_str_type(self, storage_with_ocr_tmp_dir: Storage, tmp_path: str) -> None:
            TestStorage._create_ocr_session_with_manifest(str(tmp_path), "doc.md", "# Hello", created=100.0)
            result = storage_with_ocr_tmp_dir.extract_last_ocr_result()
            assert isinstance(result, str)

        def test_returns_markdown_content(self, storage_with_ocr_tmp_dir: Storage, tmp_path: str) -> None:
            TestStorage._create_ocr_session_with_manifest(
                str(tmp_path), "doc.md", "# Title\n\nBody text.", created=100.0
            )
            result = storage_with_ocr_tmp_dir.extract_last_ocr_result()
            assert result == "# Title\n\nBody text."

        def test_selects_newest_by_created_timestamp(self, storage_with_ocr_tmp_dir: Storage, tmp_path: str) -> None:
            TestStorage._create_ocr_session_with_manifest(str(tmp_path), "old.md", "Old content", created=100.0)
            TestStorage._create_ocr_session_with_manifest(str(tmp_path), "new.md", "New content", created=200.0)
            result = storage_with_ocr_tmp_dir.extract_last_ocr_result()
            assert result == "New content"

        def test_raises_storage_empty_when_no_sessions(self, storage_with_ocr_tmp_dir: Storage) -> None:
            with pytest.raises(StorageEmpty):
                storage_with_ocr_tmp_dir.extract_last_ocr_result()

        def test_raises_storage_empty_when_dir_does_not_exist(self) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._ocr_dir = "/nonexistent/path/that/does/not/exist"
            with pytest.raises(StorageEmpty):
                storage.extract_last_ocr_result()

        def test_handles_empty_markdown_file(self, storage_with_ocr_tmp_dir: Storage, tmp_path: str) -> None:
            TestStorage._create_ocr_session_with_manifest(str(tmp_path), "doc.md", "", created=100.0)
            result = storage_with_ocr_tmp_dir.extract_last_ocr_result()
            assert result == ""

    class TestDisplayLastOcrResult:

        def test_returns_none(self, storage_with_ocr_tmp_dir: Storage, tmp_path: str) -> None:
            TestStorage._create_ocr_session_with_manifest(str(tmp_path), "doc.md", "# Hello", created=100.0)
            result = storage_with_ocr_tmp_dir.display_last_ocr_result()  # type: ignore[func-returns-value]
            assert result is None

        def test_prints_markdown_content(
            self, storage_with_ocr_tmp_dir: Storage, tmp_path: str, capsys: pytest.CaptureFixture[str]
        ) -> None:
            TestStorage._create_ocr_session_with_manifest(
                str(tmp_path), "doc.md", "# Title\n\nBody text.", created=100.0
            )
            storage_with_ocr_tmp_dir.display_last_ocr_result()
            captured = capsys.readouterr()
            assert "# Title" in captured.out
            assert "Body text." in captured.out

        def test_returns_none_when_no_sessions(self, storage_with_ocr_tmp_dir: Storage) -> None:
            result = storage_with_ocr_tmp_dir.display_last_ocr_result()  # type: ignore[func-returns-value]
            assert result is None

        def test_prints_warning_when_no_sessions(self, storage_with_ocr_tmp_dir: Storage) -> None:
            with patch("gptcli.src.common.storage.print_formatted_text") as mock_print:
                storage_with_ocr_tmp_dir.display_last_ocr_result()
                mock_print.assert_called_once()
                call_args = str(mock_print.call_args)
                assert "No OCR results found in storage" in call_args

    class TestStoreMessagesEncrypted:

        @pytest.fixture
        def encryption(self) -> Encryption:
            key = os.urandom(32)
            return Encryption(key=key)

        @pytest.fixture
        def storage_with_encryption(self, tmp_path: str, encryption: Encryption) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=encryption)
            storage._chat_dir = str(tmp_path)
            return storage

        @staticmethod
        def _create_messages() -> Messages:
            factory = MessageFactory(provider=ProviderNames.MISTRAL.value)
            messages = Messages()
            msg = factory.user_message(role="user", content="Hello!", model="mistral-large-latest")
            messages.add(msg)
            return messages

        def test_creates_enc_file_when_encryption_provided(
            self, storage_with_encryption: Storage, tmp_path: str
        ) -> None:
            messages = self._create_messages()
            storage_with_encryption.store_messages(messages)
            # Check inside the UUID directory for session.json.enc
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            assert len(subdirs) == 1
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            assert os.path.exists(os.path.join(session_dir, "session.json.enc"))

        def test_enc_file_content_is_not_readable_json(self, storage_with_encryption: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_encryption.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            filepath = os.path.join(session_dir, "session.json.enc")
            with open(filepath, "rb") as f:
                content = f.read()
            with pytest.raises(Exception):
                json.loads(content)

        def test_does_not_create_cleartext_session_json(self, storage_with_encryption: Storage, tmp_path: str) -> None:
            messages = self._create_messages()
            storage_with_encryption.store_messages(messages)
            subdirs = [d for d in os.listdir(tmp_path) if os.path.isdir(os.path.join(tmp_path, d))]
            session_dir = os.path.join(str(tmp_path), subdirs[0])
            assert not os.path.exists(os.path.join(session_dir, "session.json"))

    class TestExtractMessagesEncrypted:

        @pytest.fixture
        def key(self) -> bytes:
            return os.urandom(32)

        @pytest.fixture
        def encryption(self, key: bytes) -> Encryption:
            return Encryption(key=key)

        @pytest.fixture
        def storage_with_encryption(self, tmp_path: str, encryption: Encryption) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=encryption)
            storage._chat_dir = str(tmp_path)
            return storage

        @staticmethod
        def _create_encrypted_chat_session(
            tmp_path: str, content: str, created: float, encryption: Encryption
        ) -> None:
            """Create an encrypted test chat session with UUID directory."""
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(tmp_path, session_uuid)
            os.makedirs(session_dir)
            chat_data: dict[str, list[dict[str, Any]]] = {
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                        "model": "mistral-large-latest",
                        "provider": "mistral",
                        "is_reply": False,
                        "created": 1704067200.0,
                        "uuid": "00000000-0000-0000-0000-000000000000",
                        "tokens": 5,
                    }
                ]
            }
            json_bytes = json.dumps(chat_data).encode("utf-8")
            encrypted = encryption.encrypt(json_bytes)
            filepath = os.path.join(session_dir, "session.json.enc")
            with open(filepath, "wb") as f:
                f.write(encrypted)

            # Update manifest (encrypted too)
            manifest_path = os.path.join(tmp_path, _MANIFEST_FILENAME)
            entries: list[dict[str, Any]] = []
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf8") as f:
                    entries = json.load(f)
            entries.append({"uuid": session_uuid, "created": created})
            manifest_bytes = json.dumps(entries).encode("utf-8")
            encrypted_manifest = encryption.encrypt(manifest_bytes)
            with open(manifest_path + ".enc", "wb") as f:
                f.write(encrypted_manifest)

        def test_extracts_from_enc_file(
            self, storage_with_encryption: Storage, tmp_path: str, encryption: Encryption
        ) -> None:
            self._create_encrypted_chat_session(str(tmp_path), "Hello encrypted", created=100.0, encryption=encryption)
            messages = storage_with_encryption.extract_messages()
            assert messages is not None
            first_message = next(iter(messages))
            assert first_message.content == "Hello encrypted"

        def test_roundtrip_store_then_extract_with_encryption(self, storage_with_encryption: Storage) -> None:
            factory = MessageFactory(provider=ProviderNames.MISTRAL.value)
            messages = Messages()
            msg = factory.user_message(role="user", content="Roundtrip test", model="mistral-large-latest")
            messages.add(msg)
            storage_with_encryption.store_messages(messages)
            extracted = storage_with_encryption.extract_messages()
            assert extracted is not None
            first_message = next(iter(extracted))
            assert first_message.content == "Roundtrip test"

        def test_selects_newest_enc_session_by_created(
            self, storage_with_encryption: Storage, tmp_path: str, encryption: Encryption
        ) -> None:
            self._create_encrypted_chat_session(str(tmp_path), "Old message", created=100.0, encryption=encryption)
            self._create_encrypted_chat_session(str(tmp_path), "New message", created=200.0, encryption=encryption)
            messages = storage_with_encryption.extract_messages()
            assert messages is not None
            first_message = next(iter(messages))
            assert first_message.content == "New message"

    class TestStoreOcrResultEncrypted:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        @pytest.fixture
        def storage_with_encryption(self, tmp_path: str, encryption: Encryption) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=encryption)
            storage._ocr_dir = str(tmp_path)
            return storage

        def test_creates_enc_files_for_markdown_metadata_and_images(
            self, storage_with_encryption: Storage, tmp_path: str
        ) -> None:
            session_dir = storage_with_encryption.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[("img1.png", b"fake image data")],
            )
            files = os.listdir(session_dir)
            assert "doc.md.enc" in files
            assert "metadata.json.enc" in files
            assert "img1.png.enc" in files
            assert "doc.md" not in files
            assert "metadata.json" not in files
            assert "img1.png" not in files

        def test_enc_markdown_content_is_not_readable(self, storage_with_encryption: Storage, tmp_path: str) -> None:
            session_dir = storage_with_encryption.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test content here",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            enc_file = os.path.join(session_dir, "doc.md.enc")
            with open(enc_file, "rb") as f:
                content = f.read()
            assert b"# Test content here" not in content

        def test_metadata_json_enc_is_not_readable_json(self, storage_with_encryption: Storage, tmp_path: str) -> None:
            session_dir = storage_with_encryption.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# Test",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            enc_file = os.path.join(session_dir, "metadata.json.enc")
            with open(enc_file, "rb") as f:
                content = f.read()
            with pytest.raises(Exception):
                json.loads(content)

    class TestExtractLastOcrResultEncrypted:

        @pytest.fixture
        def encryption(self) -> Encryption:
            return Encryption(key=os.urandom(32))

        @pytest.fixture
        def storage_with_encryption(self, tmp_path: str, encryption: Encryption) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=encryption)
            storage._ocr_dir = str(tmp_path)
            return storage

        @staticmethod
        def _create_encrypted_ocr_session(
            tmp_path: str, md_filename: str, md_content: str, created: float, encryption: Encryption
        ) -> str:
            """Create an encrypted test OCR session with UUID directory and manifest."""
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(tmp_path, session_uuid)
            os.makedirs(session_dir)
            encrypted = encryption.encrypt(md_content.encode("utf-8"))
            enc_path = os.path.join(session_dir, md_filename + ".enc")
            with open(enc_path, "wb") as f:
                f.write(encrypted)

            # Update manifest
            manifest_path = os.path.join(tmp_path, _MANIFEST_FILENAME)
            entries: list[dict[str, Any]] = []
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf8") as f:
                    entries = json.load(f)
            entries.append({"uuid": session_uuid, "created": created})
            with open(manifest_path, "w", encoding="utf8") as f:
                json.dump(entries, f)

            return session_dir

        def test_extracts_and_decrypts_markdown(
            self, storage_with_encryption: Storage, tmp_path: str, encryption: Encryption
        ) -> None:
            self._create_encrypted_ocr_session(
                str(tmp_path), "doc.md", "# Encrypted content", created=100.0, encryption=encryption
            )
            result = storage_with_encryption.extract_last_ocr_result()
            assert result == "# Encrypted content"

        def test_roundtrip_store_then_extract_with_encryption(self, storage_with_encryption: Storage) -> None:
            storage_with_encryption.store_ocr_result(
                source="/path/to/doc.pdf",
                markdown_content="# OCR roundtrip",
                model=MistralModelsOcr.MISTRAL_OCR.value,
                page_count=1,
                image_data=[],
            )
            result = storage_with_encryption.extract_last_ocr_result()
            assert result == "# OCR roundtrip"

        def test_selects_newest_enc_session_by_created(
            self, storage_with_encryption: Storage, tmp_path: str, encryption: Encryption
        ) -> None:
            self._create_encrypted_ocr_session(
                str(tmp_path), "old.md", "Old content", created=100.0, encryption=encryption
            )
            self._create_encrypted_ocr_session(
                str(tmp_path), "new.md", "New content", created=200.0, encryption=encryption
            )
            result = storage_with_encryption.extract_last_ocr_result()
            assert result == "New content"

    class TestEncryptionRequiredError:

        def test_extract_messages_returns_none_when_enc_file_without_key(self, tmp_path: str) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            storage._chat_dir = str(tmp_path)

            # Create a session with encrypted data and manifest
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(str(tmp_path), session_uuid)
            os.makedirs(session_dir)
            filepath = os.path.join(session_dir, "session.json.enc")
            with open(filepath, "wb") as f:
                f.write(b"encrypted data")
            manifest_path = os.path.join(str(tmp_path), _MANIFEST_FILENAME)
            with open(manifest_path, "w", encoding="utf8") as f:
                json.dump([{"uuid": session_uuid, "created": 100.0}], f)

            with patch("gptcli.src.common.storage.print_formatted_text") as mock_print:
                result = storage.extract_messages()
                assert result is None
                mock_print.assert_called_once()
                assert "Encrypted data found but no encryption key provided" in str(mock_print.call_args)

        def test_extract_last_ocr_result_returns_none_when_enc_file_without_key(self, tmp_path: str) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            storage._ocr_dir = str(tmp_path)

            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(str(tmp_path), session_uuid)
            os.makedirs(session_dir)
            enc_path = os.path.join(session_dir, "doc.md.enc")
            with open(enc_path, "wb") as f:
                f.write(b"encrypted data")
            manifest_path = os.path.join(str(tmp_path), _MANIFEST_FILENAME)
            with open(manifest_path, "w", encoding="utf8") as f:
                json.dump([{"uuid": session_uuid, "created": 100.0}], f)

            with patch("gptcli.src.common.storage.print_formatted_text") as mock_print:
                result = storage.extract_last_ocr_result()
                assert result is None
                mock_print.assert_called_once()
                assert "Encrypted data found but no encryption key provided" in str(mock_print.call_args)

    class TestWriteText:

        def test_writes_plaintext_when_no_encryption(self, tmp_path: str) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            filepath = os.path.join(str(tmp_path), "test.json")
            storage._write_text(filepath, "hello world")
            assert os.path.exists(filepath)
            assert not os.path.exists(filepath + ".enc")
            with open(filepath, "r", encoding="utf8") as f:
                assert f.read() == "hello world"

        def test_writes_encrypted_when_encryption_enabled(self, tmp_path: str) -> None:
            enc = Encryption(key=os.urandom(32))
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=enc)
            filepath = os.path.join(str(tmp_path), "test.json")
            storage._write_text(filepath, "hello world")
            assert os.path.exists(filepath + ".enc")
            assert not os.path.exists(filepath)

        def test_encrypted_content_is_decryptable(self, tmp_path: str) -> None:
            enc = Encryption(key=os.urandom(32))
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=enc)
            filepath = os.path.join(str(tmp_path), "test.json")
            storage._write_text(filepath, "hello world")
            decrypted = enc.decrypt_file(filepath + ".enc")
            assert decrypted is not None
            assert decrypted.decode("utf-8") == "hello world"

    class TestReadText:

        def test_reads_plaintext_file(self, tmp_path: str) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w", encoding="utf8") as f:
                f.write("hello world")
            assert storage._read_text(filepath) == "hello world"

        def test_reads_encrypted_file_when_encryption_enabled(self, tmp_path: str) -> None:
            enc = Encryption(key=os.urandom(32))
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=enc)
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w", encoding="utf8") as f:
                f.write("plaintext content")
            enc.encrypt_file(filepath)
            assert storage._read_text(filepath) == "plaintext content"

        def test_returns_none_when_encrypted_file_without_key(self, tmp_path: str) -> None:
            enc = Encryption(key=os.urandom(32))
            storage_no_key = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w", encoding="utf8") as f:
                f.write("content")
            enc.encrypt_file(filepath)
            with patch("gptcli.src.common.storage.print_formatted_text"):
                assert storage_no_key._read_text(filepath) is None

        def test_returns_none_when_no_file_exists(self, tmp_path: str) -> None:
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=None)
            filepath = os.path.join(str(tmp_path), "nonexistent.json")
            assert storage._read_text(filepath) is None

        def test_prefers_encrypted_file_over_plaintext(self, tmp_path: str) -> None:
            enc = Encryption(key=os.urandom(32))
            storage = Storage(provider=ProviderNames.MISTRAL.value, encryption=enc)
            filepath = os.path.join(str(tmp_path), "test.json")
            with open(filepath, "w", encoding="utf8") as f:
                f.write("old plaintext")
            enc_path = filepath + ".enc"
            encrypted = enc.encrypt(b"new encrypted content")
            with open(enc_path, "wb") as f:
                f.write(encrypted)
            assert storage._read_text(filepath) == "new encrypted content"

    class TestManifestOperations:

        @pytest.fixture
        def storage(self, tmp_path: str) -> Storage:
            storage = Storage(provider=ProviderNames.MISTRAL.value)
            storage._chat_dir = str(tmp_path)
            return storage

        def test_read_manifest_returns_empty_list_when_no_manifest(self, storage: Storage, tmp_path: str) -> None:
            entries = storage._read_manifest(str(tmp_path))
            assert entries == []

        def test_write_and_read_manifest(self, storage: Storage, tmp_path: str) -> None:
            entries = [{"uuid": "test-uuid", "created": 123.0}]
            storage._write_manifest(str(tmp_path), entries)
            result = storage._read_manifest(str(tmp_path))
            assert result == entries

        def test_append_to_manifest(self, storage: Storage, tmp_path: str) -> None:
            storage._append_to_manifest(str(tmp_path), "uuid-1", 100.0)
            storage._append_to_manifest(str(tmp_path), "uuid-2", 200.0)
            entries = storage._read_manifest(str(tmp_path))
            assert len(entries) == 2
            assert entries[0]["uuid"] == "uuid-1"
            assert entries[1]["uuid"] == "uuid-2"

        def test_find_latest_uuid(self, storage: Storage, tmp_path: str) -> None:
            os.makedirs(os.path.join(str(tmp_path), "uuid-old"))
            os.makedirs(os.path.join(str(tmp_path), "uuid-new"))
            storage._append_to_manifest(str(tmp_path), "uuid-old", 100.0)
            storage._append_to_manifest(str(tmp_path), "uuid-new", 200.0)
            assert storage._find_latest_uuid(str(tmp_path)) == "uuid-new"

        def test_find_latest_uuid_returns_none_when_empty(self, storage: Storage, tmp_path: str) -> None:
            assert storage._find_latest_uuid(str(tmp_path)) is None

        def test_find_latest_uuid_skips_deleted_directories(self, storage: Storage, tmp_path: str) -> None:
            os.makedirs(os.path.join(str(tmp_path), "uuid-exists"))
            storage._append_to_manifest(str(tmp_path), "uuid-deleted", 200.0)
            storage._append_to_manifest(str(tmp_path), "uuid-exists", 100.0)
            assert storage._find_latest_uuid(str(tmp_path)) == "uuid-exists"
