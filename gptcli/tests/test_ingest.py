"""Tests for the ingestion feature in the project"""
import os
import pytest

from gptcli.definitions import PROJECT_ROOT_DIRECTORY
from gptcli.src.ingest import PDF

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

    def test_should_return_a_string_with_text(self):
        test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/true-pdf-sample-1.pdf")
        pdf = PDF(filepath=test_file_filepath)
        text = pdf.extract_text()
        length = len(text)
        assert length > 0

    def test_should_return_true_if_file_is_pdf(self):
        test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/true-pdf-sample-1.pdf")
        pdf = PDF(filepath=test_file_filepath)
        file_is_pdf = pdf.is_pdf()
        assert file_is_pdf

    def test_should_return_false_if_file_is_not_a_pdf(self):
        test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/empty_docx_file.docx")
        pdf = PDF(filepath=test_file_filepath)
        file_is_pdf = pdf.is_pdf()
        assert not file_is_pdf

    def test_should_return_false_if_file_is_not_supported(self):
        test_file_filepath = os.path.join(PROJECT_ROOT_DIRECTORY, "gptcli/tests/data/ingest/sample1.parquet")
        pdf = PDF(filepath=test_file_filepath)
        file_is_pdf = pdf.is_pdf()
        assert not file_is_pdf
