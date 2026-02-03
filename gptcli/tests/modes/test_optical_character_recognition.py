"""Tests for optical_character_recognition.py."""

import base64
import io
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage

from gptcli.constants import MISTRAL_API_KEY
from gptcli.src.common.constants import MistralModelsOcr, ProviderNames
from gptcli.src.modes.optical_character_recognition import (
    OpticalCharacterRecognition,
)

TEST_DATA_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data", "optical_character_recognition")
SAMPLE_PDF_PATH: str = os.path.join(TEST_DATA_DIR, "sample.pdf")


# =============================================================================
# Unit Tests: _encode_pdf_to_base64
# =============================================================================
class TestEncodePdfToBase64:

    @pytest.fixture
    def ocr_instance(self) -> OpticalCharacterRecognition:
        """Fixture providing an OCR instance with mocked environment."""
        with patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key"}):
            return OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=[],
            )

    def test_returns_str_type(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._encode_pdf_to_base64(SAMPLE_PDF_PATH)
        assert isinstance(result, str)

    def test_returns_non_empty_string(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._encode_pdf_to_base64(SAMPLE_PDF_PATH)
        assert len(result) > 0

    def test_returns_decodable_base64(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._encode_pdf_to_base64(SAMPLE_PDF_PATH)
        decoded = base64.b64decode(result)
        assert decoded[:4] == b"%PDF"

    def test_raises_file_not_found_error_on_missing_file(self, ocr_instance: OpticalCharacterRecognition) -> None:
        with pytest.raises(FileNotFoundError):
            ocr_instance._encode_pdf_to_base64("/nonexistent/path/file.pdf")


# =============================================================================
# Unit Tests: _parse_ocr_response
# =============================================================================
class TestParseOcrResponse:

    @pytest.fixture
    def ocr_instance(self) -> OpticalCharacterRecognition:
        """Fixture providing an OCR instance with mocked environment."""
        with patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key"}):
            return OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=[],
            )

    @pytest.fixture
    def mock_single_page_response(self) -> MagicMock:
        """Mock Response object with single page OCR result."""
        mock_response = MagicMock()
        mock_response.content = b"""{
            "pages": [
                {
                    "index": 0,
                    "markdown": "This is sample text.",
                    "images": []
                }
            ]
        }"""
        return mock_response

    @pytest.fixture
    def mock_multi_page_response(self) -> MagicMock:
        """Mock Response object with multiple page OCR result."""
        mock_response = MagicMock()
        mock_response.content = b"""{
            "pages": [
                {
                    "index": 0,
                    "markdown": "Page one content.",
                    "images": []
                },
                {
                    "index": 1,
                    "markdown": "Page two content.",
                    "images": []
                }
            ]
        }"""
        return mock_response

    def test_returns_str_type(
        self, ocr_instance: OpticalCharacterRecognition, mock_single_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_single_page_response)
        assert isinstance(result, str)

    def test_includes_page_header(
        self, ocr_instance: OpticalCharacterRecognition, mock_single_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_single_page_response)
        assert "### Page 1" in result

    def test_includes_page_one_header_for_multi_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_multi_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_multi_page_response)
        assert "### Page 1" in result

    def test_includes_page_two_header_for_multi_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_multi_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_multi_page_response)
        assert "### Page 2" in result

    def test_includes_page_one_content_for_multi_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_multi_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_multi_page_response)
        assert "Page one content." in result

    def test_includes_page_two_content_for_multi_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_multi_page_response: MagicMock
    ) -> None:
        result, _, _ = ocr_instance._parse_ocr_response(mock_multi_page_response)
        assert "Page two content." in result

    def test_returns_tuple_with_three_elements(
        self, ocr_instance: OpticalCharacterRecognition, mock_single_page_response: MagicMock
    ) -> None:
        result = ocr_instance._parse_ocr_response(mock_single_page_response)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_returns_empty_image_list_when_no_images(
        self, ocr_instance: OpticalCharacterRecognition, mock_single_page_response: MagicMock
    ) -> None:
        _, image_filenames, _ = ocr_instance._parse_ocr_response(mock_single_page_response)
        assert image_filenames == []

    def test_returns_page_count_one_for_single_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_single_page_response: MagicMock
    ) -> None:
        _, _, page_count = ocr_instance._parse_ocr_response(mock_single_page_response)
        assert page_count == 1

    def test_returns_page_count_two_for_multi_page(
        self, ocr_instance: OpticalCharacterRecognition, mock_multi_page_response: MagicMock
    ) -> None:
        _, _, page_count = ocr_instance._parse_ocr_response(mock_multi_page_response)
        assert page_count == 2

    # =========================================================================
    # Image saving tests
    # =========================================================================

    @pytest.fixture
    def mock_response_with_single_image(self) -> MagicMock:
        img = PILImage.new("RGB", (1, 1), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf8")

        mock_response = MagicMock()
        mock_response.content = f"""{{
            "pages": [
                {{
                    "index": 0,
                    "markdown": "Text with image.",
                    "images": [
                        {{
                            "id": "img_001.png",
                            "image_base64": "data:image/png;base64,{img_base64}"
                        }}
                    ]
                }}
            ]
        }}""".encode(
            "utf8"
        )
        return mock_response

    @pytest.fixture
    def mock_response_with_multiple_images(self) -> MagicMock:
        img = PILImage.new("RGB", (1, 1), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf8")

        mock_response = MagicMock()
        mock_response.content = f"""{{
            "pages": [
                {{
                    "index": 0,
                    "markdown": "Page one.",
                    "images": [
                        {{
                            "id": "page1_img1.png",
                            "image_base64": "data:image/png;base64,{img_base64}"
                        }},
                        {{
                            "id": "page1_img2.png",
                            "image_base64": "data:image/png;base64,{img_base64}"
                        }}
                    ]
                }},
                {{
                    "index": 1,
                    "markdown": "Page two.",
                    "images": [
                        {{
                            "id": "page2_img1.png",
                            "image_base64": "data:image/png;base64,{img_base64}"
                        }}
                    ]
                }}
            ]
        }}""".encode(
            "utf8"
        )
        return mock_response

    def test_returns_image_data_list(
        self, ocr_instance: OpticalCharacterRecognition, mock_response_with_single_image: MagicMock
    ) -> None:
        _, image_data_list, _ = ocr_instance._parse_ocr_response(mock_response_with_single_image)
        assert isinstance(image_data_list, list)
        assert len(image_data_list) == 1

    def test_image_data_contains_filename_and_bytes(
        self, ocr_instance: OpticalCharacterRecognition, mock_response_with_single_image: MagicMock
    ) -> None:
        _, image_data_list, _ = ocr_instance._parse_ocr_response(mock_response_with_single_image)
        filename, data = image_data_list[0]
        assert filename == "img_001.png"
        assert isinstance(data, bytes)

    def test_image_data_is_valid_image(
        self, ocr_instance: OpticalCharacterRecognition, mock_response_with_single_image: MagicMock
    ) -> None:
        _, image_data_list, _ = ocr_instance._parse_ocr_response(mock_response_with_single_image)
        _, data = image_data_list[0]
        img = PILImage.open(io.BytesIO(data))
        assert img.size == (1, 1)

    def test_returns_multiple_images_across_pages(
        self, ocr_instance: OpticalCharacterRecognition, mock_response_with_multiple_images: MagicMock
    ) -> None:
        _, image_data_list, _ = ocr_instance._parse_ocr_response(mock_response_with_multiple_images)
        assert len(image_data_list) == 3
        filenames = [filename for filename, _ in image_data_list]
        assert filenames == ["page1_img1.png", "page1_img2.png", "page2_img1.png"]


# =============================================================================
# Unit Tests: OpticalCharacterRecognition.__init__
# =============================================================================
class TestOpticalCharacterRecognitionInit:

    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_mistral_provider_sets_correct_endpoint(self) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )

        assert ocr._ocr_endpoint == "https://api.mistral.ai/v1/ocr"

    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_mistral_provider_sets_correct_api_key(self) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )

        assert ocr._api_key == MISTRAL_API_KEY

    def test_unsupported_provider_raises_not_implemented_error(self) -> None:
        with pytest.raises(NotImplementedError):
            OpticalCharacterRecognition(
                model="some-model",
                provider="unsupported-provider",
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=[],
            )


# =============================================================================
# Unit Tests: OpticalCharacterRecognition._build_headers
# =============================================================================
class TestBuildHeaders:

    @pytest.fixture
    def ocr_instance(self) -> OpticalCharacterRecognition:
        """Fixture providing an OCR instance with mocked environment."""
        with patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key-12345"}):
            return OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=[],
            )

    @patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key-12345"})
    def test_returns_dict_type(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._build_headers()
        assert isinstance(result, dict)

    @patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key-12345"})
    def test_contains_authorization_header(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._build_headers()
        assert result["authorization"] == "Bearer test-api-key-12345"

    @patch.dict(os.environ, {MISTRAL_API_KEY: "test-api-key-12345"})
    def test_contains_content_type_header(self, ocr_instance: OpticalCharacterRecognition) -> None:
        result = ocr_instance._build_headers()
        assert result["content-type"] == "application/json"


# =============================================================================
# Unit Tests: OpticalCharacterRecognition._perform_ocr_from_filepath (mocked)
# =============================================================================
class TestPerformOcrFromFilepathUnit:

    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_raises_file_not_found_error_on_missing_file(self) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )

        with pytest.raises(FileNotFoundError):
            ocr._perform_ocr_from_filepath("/nonexistent/path.pdf")

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64encodedcontent")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_returns_tuple_with_markdown_image_data_and_page_count(
        self, _mock_encode: MagicMock, mock_post: MagicMock
    ) -> None:
        mock_post.return_value.content = b"""{
            "pages": [{"index": 0, "markdown": "Text content", "images": []}]
        }"""

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=[],
            )
            markdown, image_data, page_count = ocr._perform_ocr_from_filepath("/fake/path.pdf")

        assert isinstance(markdown, str)
        assert isinstance(image_data, list)
        assert page_count == 1


# =============================================================================
# Unit Tests: OpticalCharacterRecognition._perform_ocr_from_url (mocked)
# =============================================================================
class TestPerformOcrFromUrlUnit:

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_returns_tuple_with_markdown_image_data_and_page_count(self, mock_post: MagicMock) -> None:
        mock_post.return_value.ok = True
        mock_post.return_value.content = b"""{
            "pages": [{"index": 0, "markdown": "Text content", "images": []}]
        }"""

        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )
        markdown, image_data, page_count = ocr._perform_ocr_from_url("https://example.com/doc.pdf")

        assert isinstance(markdown, str)
        assert isinstance(image_data, list)
        assert page_count == 1


# =============================================================================
# Unit Tests: OpticalCharacterRecognition.start (mocked)
# =============================================================================
class TestStartUnit:

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_returns_none_type(self, _mock_encode: MagicMock, mock_post: MagicMock) -> None:
        mock_post.return_value.content = b"""{
            "pages": [{"index": 0, "markdown": "Text", "images": []}]
        }"""

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/path.pdf"],
            )
            result = ocr.start()

        assert result is None

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_true_prints_output(
        self, _mock_encode: MagicMock, mock_post: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_post.return_value.content = b"""{
            "pages": [{"index": 0, "markdown": "Printed content", "images": []}]
        }"""

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=True,
                filelist="",
                output_dir="",
                inputs=["/fake/path.pdf"],
            )
            ocr.start()

        captured = capsys.readouterr()
        assert "Printed content" in captured.out

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_false_does_not_print(
        self, _mock_encode: MagicMock, mock_post: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_post.return_value.content = b"""{
            "pages": [{"index": 0, "markdown": "Should not print", "images": []}]
        }"""

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/path.pdf"],
            )
            ocr.start()

        captured = capsys.readouterr()
        assert captured.out == ""


# =============================================================================
# Unit Tests: OpticalCharacterRecognition.start with --store flag (mocked)
# =============================================================================
class TestStartWithStoreFlag:

    @pytest.fixture
    def mock_ocr_response_with_image(self) -> bytes:
        img = PILImage.new("RGB", (1, 1), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf8")

        return f"""{{
            "pages": [
                {{
                    "index": 0,
                    "markdown": "# Document Title\\n\\nSome content.",
                    "images": [
                        {{
                            "id": "img_001.png",
                            "image_base64": "data:image/png;base64,{img_base64}"
                        }}
                    ]
                }},
                {{
                    "index": 1,
                    "markdown": "## Page 2\\n\\nMore content.",
                    "images": []
                }}
            ]
        }}""".encode(
            "utf8"
        )

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_store_true_calls_store_ocr_result(
        self,
        _mock_encode: MagicMock,
        mock_storage: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response_with_image: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response_with_image
        mock_storage = mock_storage.return_value

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=True,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/document.pdf"],
            )
            ocr.start()

        mock_storage.store_ocr_result.assert_called_once()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_store_true_passes_correct_source(
        self,
        _mock_encode: MagicMock,
        mock_storage: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response_with_image: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response_with_image
        mock_storage = mock_storage.return_value

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=True,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/document.pdf"],
            )
            ocr.start()

        call_kwargs = mock_storage.store_ocr_result.call_args.kwargs
        assert call_kwargs["source"] == "/fake/document.pdf"

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_store_true_passes_correct_page_count(
        self,
        _mock_encode: MagicMock,
        mock_storage: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response_with_image: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response_with_image
        mock_storage = mock_storage.return_value

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=True,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/document.pdf"],
            )
            ocr.start()

        call_kwargs = mock_storage.store_ocr_result.call_args.kwargs
        assert call_kwargs["page_count"] == 2

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_store_true_passes_image_data(
        self,
        _mock_encode: MagicMock,
        mock_storage: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response_with_image: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response_with_image
        mock_storage = mock_storage.return_value

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=True,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/document.pdf"],
            )
            ocr.start()

        call_kwargs = mock_storage.store_ocr_result.call_args.kwargs
        assert len(call_kwargs["image_data"]) == 1
        assert call_kwargs["image_data"][0][0] == "img_001.png"

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_store_false_does_not_call_store_ocr_result(
        self,
        _mock_encode: MagicMock,
        mock_storage: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response_with_image: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response_with_image
        mock_storage = mock_storage.return_value

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/document.pdf"],
            )
            ocr.start()

        mock_storage.store_ocr_result.assert_not_called()


# =============================================================================
# Unit Tests: OpticalCharacterRecognition.start with --filelist flag (mocked)
# =============================================================================
class TestStartWithFilelist:

    @pytest.fixture
    def mock_ocr_response(self) -> bytes:
        return b"""{
            "pages": [{"index": 0, "markdown": "Filelist content", "images": []}]
        }"""

    @pytest.fixture
    def filelist_file(self, tmp_path: Path) -> Path:
        """Create a temporary filelist file with sample paths."""
        filelist = tmp_path / "filelist.txt"
        filelist.write_text("/fake/doc1.pdf\n/fake/doc2.pdf\n")
        return filelist

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_processes_documents_from_filelist(
        self,
        _mock_encode: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response: bytes,
        filelist_file: Path,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist=str(filelist_file),
                output_dir="",
                inputs=[],
            )
            ocr.start()

        assert mock_post.call_count == 2

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_empty_filelist_string_does_not_open_file(
        self,
        _mock_encode: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response: bytes,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist="",
                output_dir="",
                inputs=["/fake/path.pdf"],
            )
            ocr.start()

        assert mock_post.call_count == 1

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_processes_both_inputs_and_filelist(
        self,
        _mock_encode: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response: bytes,
        filelist_file: Path,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response

        with patch("os.path.exists", return_value=True):
            ocr = OpticalCharacterRecognition(
                model=MistralModelsOcr.default(),
                provider=ProviderNames.MISTRAL.value,
                store=False,
                display_last=False,
                display=False,
                filelist=str(filelist_file),
                output_dir="",
                inputs=["/fake/input.pdf"],
            )
            ocr.start()

        assert mock_post.call_count == 3

    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_filelist_path_does_not_exist_raises_error(self) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="/nonexistent/filelist.txt",
            output_dir="",
            inputs=[],
        )

        with pytest.raises(FileNotFoundError):
            ocr.start()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_filelist_with_only_empty_lines(
        self,
        mock_post: MagicMock,
        tmp_path: Path,
    ) -> None:
        filelist = tmp_path / "empty_lines.txt"
        filelist.write_text("\n\n\n")

        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist=str(filelist),
            output_dir="",
            inputs=[],
        )
        ocr.start()

        mock_post.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_filelist_with_only_whitespace_lines(
        self,
        mock_post: MagicMock,
        tmp_path: Path,
    ) -> None:
        filelist = tmp_path / "whitespace_lines.txt"
        filelist.write_text("   \n\t\t\n  \t  \n")

        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist=str(filelist),
            output_dir="",
            inputs=[],
        )
        ocr.start()

        mock_post.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_filelist_with_nonexistent_filepath_skips_file(
        self,
        mock_post: MagicMock,
        tmp_path: Path,
    ) -> None:
        filelist = tmp_path / "nonexistent_paths.txt"
        filelist.write_text("/nonexistent/file1.pdf\n/nonexistent/file2.pdf\n")

        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist=str(filelist),
            output_dir="",
            inputs=[],
        )
        ocr.start()

        mock_post.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.object(OpticalCharacterRecognition, "_encode_pdf_to_base64", return_value="base64content")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_filelist_with_mix_of_valid_and_invalid_processes_valid_only(
        self,
        _mock_encode: MagicMock,
        mock_post: MagicMock,
        mock_ocr_response: bytes,
        tmp_path: Path,
    ) -> None:
        mock_post.return_value.content = mock_ocr_response

        valid_file = tmp_path / "valid.pdf"
        valid_file.write_bytes(b"%PDF-1.4 test content")

        filelist = tmp_path / "mixed.txt"
        filelist.write_text(f"/nonexistent/file.pdf\n{valid_file}\n/another/nonexistent.pdf\n")

        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist=str(filelist),
            output_dir="",
            inputs=[],
        )
        ocr.start()

        assert mock_post.call_count == 1

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_empty_inputs_and_empty_filelist_does_nothing(
        self,
        mock_post: MagicMock,
    ) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )
        ocr.start()

        mock_post.assert_not_called()


# =============================================================================
# Unit Tests: OpticalCharacterRecognition.start with --display-last (mocked)
# =============================================================================
class TestStartWithDisplayLast:

    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_calls_extract_and_show(self, mock_storage: MagicMock) -> None:
        mock_storage_instance = mock_storage.return_value
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=True,
            display=True,
            filelist="",
            output_dir="",
            inputs=[],
        )
        ocr.start()
        mock_storage_instance.extract_and_show_last_ocr_result_for_display.assert_called_once()

    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_returns_none(self, mock_storage: MagicMock) -> None:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=True,
            display=True,
            filelist="",
            output_dir="",
            inputs=[],
        )
        result = ocr.start()
        assert result is None

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_does_not_process_inputs(self, mock_storage: MagicMock, mock_post: MagicMock) -> None:
        mock_storage_instance = mock_storage.return_value
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=True,
            display=True,
            filelist="",
            output_dir="",
            inputs=["/fake/document.pdf"],
        )
        ocr.start()
        mock_storage_instance.extract_and_show_last_ocr_result_for_display.assert_called_once()
        mock_post.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.post")
    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_does_not_process_filelist(
        self, mock_storage: MagicMock, mock_post: MagicMock, tmp_path: Path
    ) -> None:
        mock_storage_instance = mock_storage.return_value
        filelist = tmp_path / "filelist.txt"
        filelist.write_text("/fake/doc1.pdf\n/fake/doc2.pdf\n")
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=True,
            display=True,
            filelist=str(filelist),
            output_dir="",
            inputs=[],
        )
        ocr.start()
        mock_storage_instance.extract_and_show_last_ocr_result_for_display.assert_called_once()
        mock_post.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_does_not_store(self, mock_storage: MagicMock) -> None:
        mock_storage_instance = mock_storage.return_value
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=True,
            display_last=True,
            display=True,
            filelist="",
            output_dir="",
            inputs=["/fake/document.pdf"],
        )
        ocr.start()
        mock_storage_instance.extract_and_show_last_ocr_result_for_display.assert_called_once()
        mock_storage_instance.store_ocr_result.assert_not_called()

    @patch("gptcli.src.modes.optical_character_recognition.Storage")
    @patch.dict(os.environ, {MISTRAL_API_KEY: "fake-key"})
    def test_display_last_ignores_no_display_flag(self, mock_storage: MagicMock) -> None:
        mock_storage_instance = mock_storage.return_value
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=True,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )
        ocr.start()
        mock_storage_instance.extract_and_show_last_ocr_result_for_display.assert_called_once()


# =============================================================================
# Integration Tests: Filepath Input (requires Mistral API)
# =============================================================================
class TestOcrFromFilepathIntegration:

    @pytest.fixture(scope="class")
    def ocr_filepath_result(self) -> str:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )
        markdown, _, _ = ocr._perform_ocr_from_filepath(SAMPLE_PDF_PATH)
        return markdown

    def test_returns_str_type(self, ocr_filepath_result: str) -> None:
        assert isinstance(ocr_filepath_result, str)

    def test_returns_non_empty_output(self, ocr_filepath_result: str) -> None:
        assert len(ocr_filepath_result) > 0

    def test_output_contains_expected_phrase_sample(self, ocr_filepath_result: str) -> None:
        assert "sample" in ocr_filepath_result.lower(), (
            f"Expected phrase 'sample' not found in OCR output.\n" f"Actual output:\n{ocr_filepath_result}"
        )

    def test_output_contains_expected_phrase_pdf(self, ocr_filepath_result: str) -> None:
        assert "pdf" in ocr_filepath_result.lower(), (
            f"Expected phrase 'pdf' not found in OCR output.\n" f"Actual output:\n{ocr_filepath_result}"
        )

    def test_output_contains_expected_phrase_file(self, ocr_filepath_result: str) -> None:
        assert "file" in ocr_filepath_result.lower(), (
            f"Expected phrase 'file' not found in OCR output.\n" f"Actual output:\n{ocr_filepath_result}"
        )

    def test_output_includes_page_header(self, ocr_filepath_result: str) -> None:
        assert "### Page" in ocr_filepath_result, (
            f"OCR output missing markdown page header '### Page'.\n" f"Actual output:\n{ocr_filepath_result}"
        )


# =============================================================================
# Integration Tests: URL Input (requires Mistral API)
# =============================================================================
class TestOcrFromUrlIntegration:

    TEST_IMAGE_URL: str = (
        "https://raw.githubusercontent.com/mistralai/cookbook/refs/heads/main/mistral/ocr/receipt.png"
    )

    @pytest.fixture(scope="class")
    def ocr_url_result(self) -> str:
        ocr = OpticalCharacterRecognition(
            model=MistralModelsOcr.default(),
            provider=ProviderNames.MISTRAL.value,
            store=False,
            display_last=False,
            display=False,
            filelist="",
            output_dir="",
            inputs=[],
        )
        markdown, _, _ = ocr._perform_ocr_from_url(TestOcrFromUrlIntegration.TEST_IMAGE_URL)
        return markdown

    def test_returns_str_type(self, ocr_url_result: str) -> None:
        assert isinstance(ocr_url_result, str)

    def test_returns_non_empty_output(self, ocr_url_result: str) -> None:
        assert len(ocr_url_result) > 0

    def test_output_includes_page_header(self, ocr_url_result: str) -> None:
        assert "### Page" in ocr_url_result, (
            f"OCR output missing markdown page header '### Page'.\n" f"Actual output:\n{ocr_url_result}"
        )
