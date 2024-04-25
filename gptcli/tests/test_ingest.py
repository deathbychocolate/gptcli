"""Tests for the ingestion feature in the project"""

import os

import pytest

from gptcli.definitions import PROJECT_ROOT_DIRECTORY
from gptcli.src.ingest import PDF, Text


class TestText:
    """Test ingestion with text files."""

    @pytest.fixture(scope="session")
    def setup_teardown(self):
        yield

    class TestExtractText:
        """Test the extract_text method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self):
            yield

        def test_should_return_a_string_with_text(self):
            test_file_filepath = os.path.join(
                PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/text_file_populated.txt"
            )
            txt = Text(filepath=test_file_filepath)
            text = txt.extract_text()
            length = len(text)
            assert length > 0

        def test_should_return_an_empty_string(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/text_file_empty.txt")
            txt = Text(filepath=test_file_filepath)
            text = txt.extract_text()
            length = len(text)
            assert length == 0

    class TestIsText:
        """Test the is_text method."""

        @pytest.fixture(scope="session")
        def setup_teardown(self):
            yield

        def test_should_return_true_if_file_is_text_file(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/text_file_empty.txt")
            assert Text.is_text(filepath=test_file_filepath)

        def test_should_return_false_if_file_is_not_text_file(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/true-pdf-sample-1.pdf")
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
    def setup_teardown(self):
        yield

    class TestExtractTest:
        """Test the extract_text method"""

        @pytest.fixture(scope="session")
        def setup_teardown(self):
            yield

        def test_should_return_a_string_with_text(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/true-pdf-sample-1.pdf")
            pdf = PDF(filepath=test_file_filepath)
            text = pdf.extract_text()
            length = len(text)
            assert length > 0

    class TestIsPDF:
        """Test the is_pdf method"""

        @pytest.fixture(scope="session")
        def setup_teardown(self):
            yield

        def test_should_return_true_if_file_is_pdf(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/true-pdf-sample-1.pdf")
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert file_is_pdf

        def test_should_return_false_if_file_is_not_a_pdf(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/empty_docx_file.docx")
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert not file_is_pdf

        def test_should_return_false_if_file_is_not_supported(self):
            test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/sample1.parquet")
            file_is_pdf = PDF.is_pdf(filepath=test_file_filepath)
            assert not file_is_pdf
