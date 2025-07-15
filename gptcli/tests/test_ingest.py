"""Tests for the ingestion feature in the project"""

import os
from typing import Generator

import pytest

from gptcli.constants import PROJECT_ROOT_DIRECTORY
from gptcli.src.common.ingest import PDF, Text

FILEPATH_TEXT_FILE_POPULATED: str = "gptcli/tests/data/ingest/text_file_populated.txt"
FILEPATH_TEXT_FILE_EMPTY: str = "gptcli/tests/data/ingest/text_file_empty.txt"
FILEPATH_TRUE_PDF_SAMPLE_1: str = "gptcli/tests/data/ingest/true-pdf-sample-1.pdf"
FILEPATH_TRUE_PDF_SAMPLE_Z: str = "gptcli/tests/data/ingest/true-pdf-sample-z.pdf"
FILEPATH_EMPTY_DOCX_FILE: str = "gptcli/tests/data/ingest/empty_docx_file.docx"
FILEPATH_PARQUET_1_KB: str = "gptcli/tests/data/ingest/parquet_1_kB.parquet"


class TestText:
    """Test ingestion with text files."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[None, None, None]:
        yield

    class TestExtractText:
        """Test the extract_text method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[None, None, None]:
            yield

        def test_should_return_a_string_with_text(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TEXT_FILE_POPULATED)
            txt = Text(filepath=test_file_filepath)
            text = txt.extract_text()
            length = len(text)
            assert length > 0

        def test_should_return_an_empty_string(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TEXT_FILE_EMPTY)
            txt = Text(filepath=test_file_filepath)
            text = txt.extract_text()
            length = len(text)
            assert length == 0

    class TestExists:
        """Test the _exists method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[tuple[Text, Text], None, None]:
            filepath_exists = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_1)
            filepath_exists_not = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_Z)
            txt_file_exists = Text(filepath=filepath_exists)
            txt_file_exists_not = Text(filepath=filepath_exists_not)
            yield txt_file_exists, txt_file_exists_not

        def test_should_return_true(self, setup_teardown: tuple[Text, Text]) -> None:
            txt_file_exists, _ = setup_teardown
            exists = txt_file_exists._exists()  # pylint: disable=protected-access
            assert exists is True

        def test_should_return_false(self, setup_teardown: tuple[Text, Text]) -> None:
            _, txt_file_exists_not = setup_teardown
            exists = txt_file_exists_not._exists()  # pylint: disable=protected-access
            assert exists is False

    class TestIsText:
        """Test the is_text method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[None, None, None]:
            yield

        def test_should_return_true_if_file_is_text_file(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TEXT_FILE_EMPTY)
            assert Text.is_text(filepath=test_file_filepath)

        def test_should_return_false_if_file_is_not_text_file(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_1)
            assert not Text.is_text(filepath=test_file_filepath)


class TestPDF:
    """Test the feature with the PDF file format

    The PDF files used were downloaded from:
    - https://file-examples.com/index.php/sample-documents-download/sample-pdf-download/
    - https://nlsblog.org/wp-content/uploads/2020/06/true-pdf-sample-1.pdf

    The parquet files used were downloaded from:
    - https://filesampleshub.com/format/code/parquet
    """

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[None, None, None]:
        yield

    class TestExtractText:
        """Test the extract_text method"""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[None, None, None]:
            yield

        def test_should_return_a_string_with_text(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_1)
            pdf = PDF(filepath=test_file_filepath)
            text = pdf.extract_text()
            length = len(text)
            assert length > 0

    class TestExists:
        """Test the _exists method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[tuple[PDF, PDF], None, None]:
            filepath_exists = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_1)
            filepath_exists_not = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_Z)
            pdf_file_exists = PDF(filepath=filepath_exists)
            pdf_file_exists_not = PDF(filepath=filepath_exists_not)
            yield pdf_file_exists, pdf_file_exists_not

        def test_should_return_true(self, setup_teardown: tuple[PDF, PDF]) -> None:
            pdf_file_exists, _ = setup_teardown
            exists = pdf_file_exists._exists()  # pylint: disable=protected-access
            assert exists is True

        def test_should_return_false(self, setup_teardown: tuple[PDF, PDF]) -> None:
            _, pdf_file_exists_not = setup_teardown
            exists = pdf_file_exists_not._exists()  # pylint: disable=protected-access
            assert exists is False

    class TestIsPDF:
        """Test the is_pdf method"""

        @pytest.fixture(scope="session")
        def setup_teardown(self) -> Generator[None, None, None]:
            yield

        def test_should_return_true_if_file_is_pdf(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_TRUE_PDF_SAMPLE_1)
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert file_is_pdf

        def test_should_return_false_if_file_is_not_a_pdf(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/empty_docx_file.docx")
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert not file_is_pdf

        def test_should_return_false_if_file_is_not_supported(self) -> None:
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, FILEPATH_PARQUET_1_KB)
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert not file_is_pdf
