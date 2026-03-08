"""Tests for gptcli/src/common/fts.py."""

import json
import os
import shutil
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from gptcli.constants import (
    GPTCLI_MANIFEST_FILENAME,
    GPTCLI_METADATA_FILENAME,
    GPTCLI_SESSION_FILENAME,
)
from gptcli.src.common.fts import (
    _DB_FILENAME,
    ChatFTS,
    MessageSnippet,
    OcrFTS,
    OcrHit,
    SessionHit,
    tokenize,
)


def _write_json(filepath: str, data: Any) -> None:
    with open(filepath, "w", encoding="utf-8") as fp:
        json.dump(data, fp)


def _create_session(
    chat_dir: str,
    messages: list[dict[str, Any]],
    model: str = "test-model",
    provider: str = "mistral",
    created: float = 1000.0,
) -> str:
    """Create a session directory with session.json, metadata.json, and a manifest entry."""
    session_uuid = str(uuid.uuid4())
    session_dir = os.path.join(chat_dir, session_uuid)
    os.makedirs(session_dir)

    _write_json(os.path.join(session_dir, GPTCLI_SESSION_FILENAME), {"messages": messages})
    _write_json(
        os.path.join(session_dir, GPTCLI_METADATA_FILENAME),
        {"chat": {"uuid": session_uuid, "created": created, "model": model, "provider": provider}},
    )

    manifest_path = os.path.join(chat_dir, GPTCLI_MANIFEST_FILENAME)
    entries: list[dict[str, Any]] = []
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as fp:
            entries = json.load(fp)
    entries.append({"uuid": session_uuid, "created": created})
    _write_json(manifest_path, entries)

    return session_uuid


class TestChatFTS:

    class TestBuild:

        def test_empty_directory_returns_zero(self, tmp_path: str) -> None:
            fts = ChatFTS()
            count = fts.build(str(tmp_path), encryption=None)
            assert count == 0

        def test_indexes_all_sessions(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            messages = [{"role": "user", "content": "hello world"}]
            _create_session(chat_dir, messages, created=1000.0)
            _create_session(chat_dir, messages, created=2000.0)

            fts = ChatFTS()
            count = fts.build(chat_dir, encryption=None)
            assert count == 2

        def test_creates_persistent_db_when_no_encryption(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(chat_dir, [{"role": "user", "content": "hello"}])

            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            assert os.path.exists(os.path.join(chat_dir, _DB_FILENAME))

        def test_uses_memory_db_when_encryption_enabled(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(chat_dir, [{"role": "user", "content": "hello"}])

            mock_enc = MagicMock()
            mock_enc.decrypt_file.return_value = None  # can't read encrypted files
            fts = ChatFTS()
            fts.build(chat_dir, encryption=mock_enc)
            assert not os.path.exists(os.path.join(chat_dir, _DB_FILENAME))

        def test_incremental_build_only_indexes_new_sessions(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            messages = [{"role": "user", "content": "hello world"}]
            _create_session(chat_dir, messages, created=1000.0)

            fts1 = ChatFTS()
            count1 = fts1.build(chat_dir, encryption=None)
            assert count1 == 1

            # Add a second session and rebuild
            _create_session(chat_dir, messages, created=2000.0)
            fts2 = ChatFTS()
            count2 = fts2.build(chat_dir, encryption=None)
            assert count2 == 2

        def test_handles_missing_session_directory(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            manifest_path = os.path.join(chat_dir, GPTCLI_MANIFEST_FILENAME)
            _write_json(manifest_path, [{"uuid": "nonexistent-uuid", "created": 1000.0}])

            fts = ChatFTS()
            count = fts.build(chat_dir, encryption=None)
            assert count == 0

        def test_skips_sessions_without_manifest_entry(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            dangling_dir = os.path.join(chat_dir, str(uuid.uuid4()))
            os.makedirs(dangling_dir)

            fts = ChatFTS()
            count = fts.build(chat_dir, encryption=None)
            assert count == 0

        def test_handles_encrypted_sessions_without_key(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(chat_dir, session_uuid)
            os.makedirs(session_dir)

            with open(os.path.join(session_dir, GPTCLI_SESSION_FILENAME + ".enc"), "wb") as fp:
                fp.write(b"encrypted-data")

            _write_json(os.path.join(chat_dir, GPTCLI_MANIFEST_FILENAME), [{"uuid": session_uuid, "created": 1000.0}])

            fts = ChatFTS()
            count = fts.build(chat_dir, encryption=None)
            assert count == 0

        def test_handles_encrypted_sessions_with_mock_encryption(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(chat_dir, session_uuid)
            os.makedirs(session_dir)

            session_data = json.dumps({"messages": [{"role": "user", "content": "quantum physics"}]}).encode("utf-8")
            metadata_data = json.dumps(
                {"chat": {"uuid": session_uuid, "created": 1000.0, "model": "m", "provider": "mistral"}}
            ).encode("utf-8")

            with open(os.path.join(session_dir, GPTCLI_SESSION_FILENAME + ".enc"), "wb") as fp:
                fp.write(b"ignored")
            with open(os.path.join(session_dir, GPTCLI_METADATA_FILENAME + ".enc"), "wb") as fp:
                fp.write(b"ignored")

            _write_json(os.path.join(chat_dir, GPTCLI_MANIFEST_FILENAME), [{"uuid": session_uuid, "created": 1000.0}])

            mock_enc = MagicMock()
            mock_enc.decrypt_file.side_effect = lambda p: (
                session_data if GPTCLI_SESSION_FILENAME in p else metadata_data
            )

            fts = ChatFTS()
            count = fts.build(chat_dir, encryption=mock_enc)
            assert count == 1

    class TestSearch:

        @pytest.fixture
        def populated_fts(self, tmp_path: str) -> ChatFTS:
            chat_dir = str(tmp_path)
            _create_session(
                chat_dir,
                [
                    {"role": "user", "content": "explain quantum entanglement"},
                    {"role": "assistant", "content": "Quantum entanglement is a phenomenon"},
                ],
                model="mistral-large",
                created=1000.0,
            )
            _create_session(
                chat_dir,
                [{"role": "user", "content": "what is machine learning"}],
                model="gpt-5-mini",
                created=2000.0,
            )
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            return fts

        def test_returns_matching_session(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("quantum")
            assert len(results) == 1
            assert isinstance(results[0], SessionHit)

        def test_case_insensitive_match(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("QUANTUM")
            assert len(results) == 1

        def test_and_semantics_requires_all_tokens(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("quantum machine")
            assert len(results) == 0

        def test_returns_empty_for_no_match(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("xyzzy404notfound")
            assert len(results) == 0

        def test_empty_query_returns_all_sessions(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("")
            assert len(results) == 2

        def test_whitespace_query_returns_all_sessions(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("   ")
            assert len(results) == 2

        def test_empty_query_orders_by_recency(self, populated_fts: ChatFTS) -> None:
            results = populated_fts.search("")
            assert results[0].created > results[1].created

        def test_returns_at_most_50_results(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            for i in range(60):
                _create_session(chat_dir, [{"role": "user", "content": "common token here"}], created=float(i))
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            assert len(fts.search("common")) == 50

        def test_empty_query_returns_all_indexed_sessions(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            for i in range(60):
                _create_session(chat_dir, [{"role": "user", "content": "hello"}], created=float(i))
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            assert len(fts.search("")) == 60

        def test_result_has_correct_metadata(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(
                chat_dir,
                [{"role": "user", "content": "hello world"}],
                model="my-model",
                provider="mistral",
                created=1234567890.0,
            )
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            results = fts.search("hello")
            assert len(results) == 1
            hit = results[0]
            assert hit.model == "my-model"
            assert hit.provider == "mistral"
            assert hit.message_count == 1
            assert hit.created == pytest.approx(1234567890.0)

        def test_snippets_include_matching_messages(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(
                chat_dir,
                [
                    {"role": "user", "content": "tell me about quantum"},
                    {"role": "assistant", "content": "Quantum is fascinating"},
                ],
                created=1000.0,
            )
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            results = fts.search("quantum")
            assert len(results) == 1
            snippets = results[0].snippets
            assert len(snippets) > 0
            assert all(isinstance(s, MessageSnippet) for s in snippets)
            assert any("quantum" in s.content.lower() for s in snippets)

        def test_snippets_are_single_line(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(
                chat_dir,
                [{"role": "user", "content": "quantum\nline2\nline3"}],
                created=1000.0,
            )
            fts = ChatFTS()
            fts.build(chat_dir, encryption=None)
            results = fts.search("quantum")
            for snippet in results[0].snippets:
                assert "\n" not in snippet.content

    class TestIncrementalBuild:

        def test_removes_deleted_sessions_from_index(self, tmp_path: str) -> None:
            chat_dir = str(tmp_path)
            _create_session(chat_dir, [{"role": "user", "content": "hello world"}], created=1000.0)
            session_b = _create_session(chat_dir, [{"role": "user", "content": "goodbye world"}], created=2000.0)

            fts1 = ChatFTS()
            fts1.build(chat_dir, encryption=None)
            assert len(fts1.search("goodbye")) == 1

            # Remove session B from manifest and disk
            shutil.rmtree(os.path.join(chat_dir, session_b))
            manifest_path = os.path.join(chat_dir, GPTCLI_MANIFEST_FILENAME)
            with open(manifest_path, "r", encoding="utf-8") as fp:
                entries = json.load(fp)
            entries = [e for e in entries if e["uuid"] != session_b]
            _write_json(manifest_path, entries)

            fts2 = ChatFTS()
            count = fts2.build(chat_dir, encryption=None)
            assert count == 1
            assert len(fts2.search("goodbye")) == 0

    class TestTokenize:

        def test_lowercases_input(self) -> None:
            assert tokenize("Hello WORLD") == ["hello", "world"]

        def test_strips_punctuation(self) -> None:
            assert tokenize("hello, world!") == ["hello", "world"]

        def test_splits_on_whitespace(self) -> None:
            assert tokenize("one two three") == ["one", "two", "three"]

        def test_returns_only_alphanumeric(self) -> None:
            assert tokenize("foo@bar #baz 123") == ["foo", "bar", "baz", "123"]

        def test_empty_string_returns_empty_list(self) -> None:
            assert tokenize("") == []

        def test_numbers_are_included(self) -> None:
            assert tokenize("gpt4 model2024") == ["gpt4", "model2024"]


def _create_ocr_session(
    ocr_dir: str,
    markdown_content: str,
    model: str = "mistral-ocr-latest",
    provider: str = "mistral",
    source_filename: str = "document.pdf",
    page_count: int = 3,
    created: float = 1000.0,
) -> str:
    """Create an OCR session directory with metadata.json, a markdown file, and a manifest entry."""
    session_uuid = str(uuid.uuid4())
    session_dir = os.path.join(ocr_dir, session_uuid)
    os.makedirs(session_dir)

    markdown_filename = "document.md"
    with open(os.path.join(session_dir, markdown_filename), "w", encoding="utf-8") as fp:
        fp.write(markdown_content)

    _write_json(
        os.path.join(session_dir, GPTCLI_METADATA_FILENAME),
        {
            "source": {"input": f"/path/to/{source_filename}", "input_type": "filepath", "filename": source_filename},
            "ocr": {
                "uuid": session_uuid,
                "created": created,
                "model": model,
                "provider": provider,
                "page_count": page_count,
            },
            "output": {"markdown_file": markdown_filename, "images": []},
        },
    )

    manifest_path = os.path.join(ocr_dir, GPTCLI_MANIFEST_FILENAME)
    entries: list[dict[str, Any]] = []
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as fp:
            entries = json.load(fp)
    entries.append({"uuid": session_uuid, "created": created})
    _write_json(manifest_path, entries)

    return session_uuid


class TestOcrFTS:

    class TestBuild:

        def test_empty_directory_returns_zero(self, tmp_path: str) -> None:
            fts = OcrFTS()
            count = fts.build(str(tmp_path), encryption=None)
            assert count == 0

        def test_indexes_all_sessions(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "hello world", created=1000.0)
            _create_ocr_session(ocr_dir, "goodbye world", created=2000.0)

            fts = OcrFTS()
            count = fts.build(ocr_dir, encryption=None)
            assert count == 2

        def test_creates_persistent_db_when_no_encryption(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "hello")

            fts = OcrFTS()
            fts.build(ocr_dir, encryption=None)
            assert os.path.exists(os.path.join(ocr_dir, _DB_FILENAME))

        def test_uses_memory_db_when_encryption_enabled(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "hello")

            mock_enc = MagicMock()
            mock_enc.decrypt_file.return_value = None
            fts = OcrFTS()
            fts.build(ocr_dir, encryption=mock_enc)
            assert not os.path.exists(os.path.join(ocr_dir, _DB_FILENAME))

        def test_incremental_build_only_indexes_new_sessions(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "first document", created=1000.0)

            fts1 = OcrFTS()
            count1 = fts1.build(ocr_dir, encryption=None)
            assert count1 == 1

            _create_ocr_session(ocr_dir, "second document", created=2000.0)
            fts2 = OcrFTS()
            count2 = fts2.build(ocr_dir, encryption=None)
            assert count2 == 2

        def test_handles_missing_session_directory(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            manifest_path = os.path.join(ocr_dir, GPTCLI_MANIFEST_FILENAME)
            _write_json(manifest_path, [{"uuid": "nonexistent-uuid", "created": 1000.0}])

            fts = OcrFTS()
            count = fts.build(ocr_dir, encryption=None)
            assert count == 0

        def test_handles_encrypted_sessions_with_mock_encryption(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            session_uuid = str(uuid.uuid4())
            session_dir = os.path.join(ocr_dir, session_uuid)
            os.makedirs(session_dir)

            markdown_content = "## Invoice\n\nTotal: $100"
            metadata = {
                "source": {"input": "/path/to/invoice.pdf", "input_type": "filepath", "filename": "invoice.pdf"},
                "ocr": {
                    "uuid": session_uuid,
                    "created": 1000.0,
                    "model": "mistral-ocr-latest",
                    "provider": "mistral",
                    "page_count": 1,
                },
                "output": {"markdown_file": "invoice.md", "images": []},
            }

            with open(os.path.join(session_dir, "invoice.md.enc"), "wb") as fp:
                fp.write(b"ignored")
            with open(os.path.join(session_dir, GPTCLI_METADATA_FILENAME + ".enc"), "wb") as fp:
                fp.write(b"ignored")

            _write_json(os.path.join(ocr_dir, GPTCLI_MANIFEST_FILENAME), [{"uuid": session_uuid, "created": 1000.0}])

            mock_enc = MagicMock()
            mock_enc.decrypt_file.side_effect = lambda p: (
                markdown_content.encode("utf-8") if p.endswith(".md.enc") else json.dumps(metadata).encode("utf-8")
            )

            fts = OcrFTS()
            count = fts.build(ocr_dir, encryption=mock_enc)
            assert count == 1

    class TestSearch:

        @pytest.fixture
        def populated_fts(self, tmp_path: str) -> OcrFTS:
            ocr_dir = str(tmp_path)
            _create_ocr_session(
                ocr_dir,
                "## Page 1\nQuantum entanglement is a physical phenomenon.",
                model="mistral-ocr-latest",
                source_filename="quantum.pdf",
                created=1000.0,
            )
            _create_ocr_session(
                ocr_dir,
                "## Page 1\nMachine learning algorithms and neural networks.",
                model="mistral-ocr-latest",
                source_filename="ml_paper.pdf",
                created=2000.0,
            )
            fts = OcrFTS()
            fts.build(ocr_dir, encryption=None)
            return fts

        def test_returns_matching_session(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("quantum")
            assert len(results) == 1
            assert isinstance(results[0], OcrHit)

        def test_case_insensitive_match(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("QUANTUM")
            assert len(results) == 1

        def test_returns_empty_for_no_match(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("xyzzy404notfound")
            assert len(results) == 0

        def test_empty_query_returns_all_sessions(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("")
            assert len(results) == 2

        def test_whitespace_query_returns_all_sessions(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("   ")
            assert len(results) == 2

        def test_empty_query_orders_by_recency(self, populated_fts: OcrFTS) -> None:
            results = populated_fts.search("")
            assert results[0].created > results[1].created

        def test_result_has_correct_metadata(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(
                ocr_dir,
                "Invoice content here",
                model="mistral-ocr-latest",
                provider="mistral",
                source_filename="invoice.pdf",
                page_count=5,
                created=1234567890.0,
            )
            fts = OcrFTS()
            fts.build(ocr_dir, encryption=None)
            results = fts.search("invoice")
            assert len(results) == 1
            hit = results[0]
            assert hit.model == "mistral-ocr-latest"
            assert hit.provider == "mistral"
            assert hit.source_filename == "invoice.pdf"
            assert hit.page_count == 5
            assert hit.created == pytest.approx(1234567890.0)

        def test_snippet_is_single_line(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "line one\nline two\nline three", created=1000.0)
            fts = OcrFTS()
            fts.build(ocr_dir, encryption=None)
            results = fts.search("")
            assert len(results) == 1
            assert "\n" not in results[0].snippet

        def test_snippet_is_truncated_to_120_chars(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            long_content = "word " * 100
            _create_ocr_session(ocr_dir, long_content, created=1000.0)
            fts = OcrFTS()
            fts.build(ocr_dir, encryption=None)
            results = fts.search("")
            assert len(results) == 1
            assert len(results[0].snippet) <= 123  # 120 chars + "..."

    class TestIncrementalBuild:

        def test_removes_deleted_sessions_from_index(self, tmp_path: str) -> None:
            ocr_dir = str(tmp_path)
            _create_ocr_session(ocr_dir, "first document content", created=1000.0)
            session_b = _create_ocr_session(ocr_dir, "second document content", created=2000.0)

            fts1 = OcrFTS()
            fts1.build(ocr_dir, encryption=None)
            assert len(fts1.search("second")) == 1

            shutil.rmtree(os.path.join(ocr_dir, session_b))
            manifest_path = os.path.join(ocr_dir, GPTCLI_MANIFEST_FILENAME)
            with open(manifest_path, "r", encoding="utf-8") as fp:
                entries = json.load(fp)
            entries = [e for e in entries if e["uuid"] != session_b]
            _write_json(manifest_path, entries)

            fts2 = OcrFTS()
            count = fts2.build(ocr_dir, encryption=None)
            assert count == 1
            assert len(fts2.search("second")) == 0
