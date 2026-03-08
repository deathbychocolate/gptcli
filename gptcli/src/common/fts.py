"""SQLite FTS5-backed full-text search index for chat and OCR sessions."""

import json
import os
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from os import path
from typing import Any, Generic, TypeVar

from gptcli.constants import (
    GPTCLI_MANIFEST_FILENAME,
    GPTCLI_METADATA_FILENAME,
    GPTCLI_SESSION_FILENAME,
)
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.file_io import read_text_file

_SNIPPET_MAX_LENGTH: int = 120
_MAX_RESULTS: int = 50
_DB_FILENAME: str = "search.db"

T = TypeVar("T")


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _placeholders(n: int) -> str:
    return ",".join("?" * n)


def _load_manifest(storage_dir: str, encryption: Encryption | None) -> list[dict[str, Any]]:
    raw = read_text_file(path.join(storage_dir, GPTCLI_MANIFEST_FILENAME), encryption)
    if raw is None:
        return []
    try:
        result: list[dict[str, Any]] = json.loads(raw)
        return result
    except json.JSONDecodeError:
        return []


def _load_metadata(session_dir: str, encryption: Encryption | None) -> dict[str, Any] | None:
    raw = read_text_file(path.join(session_dir, GPTCLI_METADATA_FILENAME), encryption)
    if raw is None:
        return None
    try:
        metadata: dict[str, Any] = json.loads(raw)
        return metadata
    except json.JSONDecodeError:
        return None


@dataclass
class MessageSnippet:
    """A truncated message used as a search result preview.

    Attributes:
        role: The role of the message sender (e.g. 'user', 'assistant').
        content: The message content, truncated to 120 characters, newlines removed.
    """

    role: str
    content: str


@dataclass
class SessionHit:
    """A search result representing a matching chat session.

    Attributes:
        uuid: The unique identifier for the session.
        created: The session creation timestamp (epoch seconds).
        model: The model used in the session.
        provider: The provider name.
        message_count: Total number of messages in the session.
        snippets: First user message and first assistant message from the session.
    """

    uuid: str
    created: float
    model: str
    provider: str
    message_count: int
    snippets: list[MessageSnippet]

    @property
    def created_display(self) -> str:
        """Return the creation timestamp formatted for display."""
        return datetime.fromtimestamp(self.created).strftime("%Y-%m-%d %H:%M")


@dataclass
class OcrHit:
    """A search result representing a matching OCR session.

    Attributes:
        uuid: The unique identifier for the session.
        created: The session creation timestamp (epoch seconds).
        model: The OCR model used in the session.
        provider: The provider name.
        source_filename: The filename of the source document.
        page_count: Total number of pages processed.
        snippet: First 120 characters of the Markdown output, newlines removed.
    """

    uuid: str
    created: float
    model: str
    provider: str
    source_filename: str
    page_count: int
    snippet: str

    @property
    def created_display(self) -> str:
        """Return the creation timestamp formatted for display."""
        return datetime.fromtimestamp(self.created).strftime("%Y-%m-%d %H:%M")


class _BaseFTS(ABC, Generic[T]):
    """Abstract base for SQLite FTS5-backed search indexes.

    Subclasses define schema, column selection, session indexing, and result
    construction. The shared build, search, and incremental-update logic lives here.
    """

    def __init__(self) -> None:
        self.__conn: sqlite3.Connection | None = None

    @property
    def _conn(self) -> sqlite3.Connection:
        if self.__conn is None:
            raise RuntimeError("Call build() before using the index.")
        return self.__conn

    def build(self, storage_dir: str, encryption: Encryption | None) -> int:
        """Build or incrementally update the FTS index.

        Args:
            storage_dir (str): Path to the provider's storage directory.
            encryption (Encryption | None): Encryption instance or None.

        Returns:
            int: Total number of sessions in the index after building.
        """
        in_memory = encryption is not None
        db_path = ":memory:" if in_memory else path.join(storage_dir, _DB_FILENAME)
        self.__conn = sqlite3.connect(db_path)
        self.__conn.execute("PRAGMA journal_mode=WAL")
        self._create_schema()
        manifest = _load_manifest(storage_dir, encryption)
        if in_memory:
            return self._full_build(storage_dir, manifest, encryption)
        return self._incremental_build(storage_dir, manifest, encryption)

    def search(self, query: str) -> list[T]:
        """Search sessions using FTS5 BM25 ranking, or return recent sessions for an empty query.

        Args:
            query (str): The search query string. Empty string returns the most recent sessions.

        Returns:
            list[T]: Up to 50 matching sessions ordered by relevance (or recency if no query).
        """
        if not query.strip():
            return self._all_sessions()

        tokens = tokenize(query)
        if not tokens:
            return []

        cols = self._select_columns()
        prefixed = ", ".join(f"s.{c.strip()}" for c in cols.split(","))
        try:
            rows = self._conn.execute(
                f"""
                SELECT {prefixed}
                FROM sessions_fts f
                JOIN sessions s ON f.uuid = s.uuid
                WHERE sessions_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (" ".join(tokens), _MAX_RESULTS),
            ).fetchall()
        except sqlite3.OperationalError:
            return []

        return self._build_hits(rows)

    def _all_sessions(self) -> list[T]:
        # No LIMIT here by design: empty query means "browse full history",
        # whereas a typed query is capped at _MAX_RESULTS by BM25 relevance.
        rows = self._conn.execute(
            f"SELECT {self._select_columns()} FROM sessions ORDER BY created DESC",
        ).fetchall()
        return self._build_hits(rows)

    def _full_build(self, storage_dir: str, manifest: list[dict[str, Any]], encryption: Encryption | None) -> int:
        count = sum(1 for entry in manifest if self._index_session(storage_dir, entry, encryption))
        self._conn.commit()
        return count

    def _incremental_build(
        self, storage_dir: str, manifest: list[dict[str, Any]], encryption: Encryption | None
    ) -> int:
        manifest_uuids = {e["uuid"] for e in manifest if "uuid" in e}
        existing_uuids = {row[0] for row in self._conn.execute("SELECT uuid FROM sessions")}

        to_delete = existing_uuids - manifest_uuids
        if to_delete:
            placeholders = _placeholders(len(to_delete))
            args = list(to_delete)
            self._conn.execute(f"DELETE FROM sessions WHERE uuid IN ({placeholders})", args)
            self._conn.execute(f"DELETE FROM sessions_fts WHERE uuid IN ({placeholders})", args)
            self._conn.execute(f"DELETE FROM {self._aux_table()} WHERE session_uuid IN ({placeholders})", args)

        to_add = [e for e in manifest if e.get("uuid") not in existing_uuids]
        added = sum(1 for entry in to_add if self._index_session(storage_dir, entry, encryption))

        self._conn.commit()
        return len(existing_uuids) - len(to_delete) + added

    @abstractmethod
    def _create_schema(self) -> None:
        """Create all required tables in the database."""

    @abstractmethod
    def _select_columns(self) -> str:
        """Return the comma-separated column list for SELECT queries (no table prefix)."""

    @abstractmethod
    def _aux_table(self) -> str:
        """Return the name of the auxiliary detail table (e.g. 'messages' or 'snippets')."""

    @abstractmethod
    def _index_session(self, storage_dir: str, entry: dict[str, Any], encryption: Encryption | None) -> bool:
        """Load and insert one session into the index.

        Returns:
            bool: True if the session was successfully indexed, False otherwise.
        """

    @abstractmethod
    def _build_hits(self, rows: list[Any]) -> list[T]:
        """Convert raw database rows into typed hit objects."""


class ChatFTS(_BaseFTS[SessionHit]):
    """SQLite FTS5-backed full-text search over chat sessions.

    When encryption is disabled a persistent ``search.db`` file is kept
    alongside the chat sessions and updated incrementally — only new
    sessions are indexed on each launch.

    When encryption is enabled an in-memory database is used so that
    decrypted content is never written to disk.
    """

    def _create_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                uuid         TEXT PRIMARY KEY,
                created      REAL NOT NULL,
                model        TEXT NOT NULL,
                provider     TEXT NOT NULL,
                message_count INTEGER NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
                uuid UNINDEXED,
                content,
                tokenize='unicode61'
            );
            CREATE TABLE IF NOT EXISTS messages (
                session_uuid TEXT    NOT NULL,
                position     INTEGER NOT NULL,
                role         TEXT    NOT NULL,
                content      TEXT    NOT NULL,
                PRIMARY KEY (session_uuid, position)
            );
        """
        )

    def _select_columns(self) -> str:
        return "uuid, created, model, provider, message_count"

    def _aux_table(self) -> str:
        return "messages"

    def _index_session(self, storage_dir: str, entry: dict[str, Any], encryption: Encryption | None) -> bool:
        session_uuid = entry.get("uuid", "")
        created = float(entry.get("created", 0.0))
        if not session_uuid:
            return False

        session_dir = path.join(storage_dir, session_uuid)
        if not os.path.isdir(session_dir):
            return False

        messages = self._load_messages(session_dir, encryption)
        if messages is None:
            return False

        metadata = _load_metadata(session_dir, encryption)
        model = metadata.get("chat", {}).get("model", "") if metadata else ""
        provider = metadata.get("chat", {}).get("provider", "") if metadata else ""

        content = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))

        self._conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
            (session_uuid, created, model, provider, len(messages)),
        )
        self._conn.execute(
            "INSERT INTO sessions_fts(uuid, content) VALUES (?, ?)",
            (session_uuid, content),
        )
        self._conn.executemany(
            "INSERT INTO messages VALUES (?, ?, ?, ?)",
            [
                (session_uuid, i, m.get("role", ""), m.get("content", ""))
                for i, m in enumerate(messages)
                if isinstance(m.get("content"), str)
            ],
        )
        return True

    def _build_hits(self, rows: list[Any]) -> list[SessionHit]:
        uuids = [row[0] for row in rows]
        snippets_by_uuid = self._build_snippets_batch(uuids)
        return [
            SessionHit(
                uuid=uuid,
                created=created,
                model=model,
                provider=provider,
                message_count=message_count,
                snippets=snippets_by_uuid.get(uuid, []),
            )
            for uuid, created, model, provider, message_count in rows
        ]

    def _build_snippets_batch(self, session_uuids: list[str]) -> dict[str, list[MessageSnippet]]:
        if not session_uuids:
            return {}
        placeholders = _placeholders(len(session_uuids))
        rows = self._conn.execute(
            f"SELECT session_uuid, role, content FROM messages WHERE session_uuid IN ({placeholders}) ORDER BY session_uuid, position",
            session_uuids,
        ).fetchall()

        result: dict[str, list[MessageSnippet]] = {uuid: [] for uuid in session_uuids}
        seen_roles: dict[str, set[str]] = {uuid: set() for uuid in session_uuids}
        for session_uuid, role, content in rows:
            if not content:
                continue
            canonical = "user" if "user" in role.lower() else "assistant"
            if canonical in seen_roles[session_uuid]:
                continue
            seen_roles[session_uuid].add(canonical)
            single_line = content.replace("\n", " ").replace("\r", " ")
            truncated = single_line[:_SNIPPET_MAX_LENGTH] + ("..." if len(single_line) > _SNIPPET_MAX_LENGTH else "")
            result[session_uuid].append(MessageSnippet(role=role, content=truncated))

        return result

    @staticmethod
    def _load_messages(session_dir: str, encryption: Encryption | None) -> list[dict[str, Any]] | None:
        raw = read_text_file(path.join(session_dir, GPTCLI_SESSION_FILENAME), encryption)
        if raw is None:
            return None
        try:
            messages: list[dict[str, Any]] = json.loads(raw).get("messages", [])
            return messages
        except (json.JSONDecodeError, AttributeError):
            return None


class OcrFTS(_BaseFTS[OcrHit]):
    """SQLite FTS5-backed full-text search over OCR sessions.

    When encryption is disabled a persistent ``search.db`` file is kept
    alongside the OCR sessions and updated incrementally — only new
    sessions are indexed on each launch.

    When encryption is enabled an in-memory database is used so that
    decrypted content is never written to disk.
    """

    def _create_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                uuid            TEXT PRIMARY KEY,
                created         REAL NOT NULL,
                model           TEXT NOT NULL,
                provider        TEXT NOT NULL,
                source_filename TEXT NOT NULL,
                page_count      INTEGER NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
                uuid UNINDEXED,
                content,
                tokenize='unicode61'
            );
            CREATE TABLE IF NOT EXISTS snippets (
                session_uuid TEXT PRIMARY KEY,
                content      TEXT NOT NULL
            );
        """
        )

    def _select_columns(self) -> str:
        return "uuid, created, model, provider, source_filename, page_count"

    def _aux_table(self) -> str:
        return "snippets"

    def _index_session(self, storage_dir: str, entry: dict[str, Any], encryption: Encryption | None) -> bool:
        session_uuid = entry.get("uuid", "")
        created = float(entry.get("created", 0.0))
        if not session_uuid:
            return False

        session_dir = path.join(storage_dir, session_uuid)
        if not os.path.isdir(session_dir):
            return False

        metadata = _load_metadata(session_dir, encryption)
        if metadata is None:
            return False

        model = metadata.get("ocr", {}).get("model", "")
        provider = metadata.get("ocr", {}).get("provider", "")
        page_count = int(metadata.get("ocr", {}).get("page_count", 0))
        source_filename = metadata.get("source", {}).get("filename", "")
        markdown_file = metadata.get("output", {}).get("markdown_file", "")

        if not markdown_file:
            return False

        markdown_raw = read_text_file(path.join(session_dir, markdown_file), encryption)
        if markdown_raw is None:
            return False

        single_line = markdown_raw.replace("\n", " ").replace("\r", " ")
        snippet = single_line[:_SNIPPET_MAX_LENGTH] + ("..." if len(single_line) > _SNIPPET_MAX_LENGTH else "")

        self._conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
            (session_uuid, created, model, provider, source_filename, page_count),
        )
        self._conn.execute(
            "INSERT INTO sessions_fts(uuid, content) VALUES (?, ?)",
            (session_uuid, markdown_raw),
        )
        self._conn.execute(
            "INSERT INTO snippets VALUES (?, ?)",
            (session_uuid, snippet),
        )
        return True

    def _build_hits(self, rows: list[Any]) -> list[OcrHit]:
        uuids = [row[0] for row in rows]
        snippets_by_uuid = self._build_snippets_batch(uuids)
        return [
            OcrHit(
                uuid=uuid,
                created=created,
                model=model,
                provider=provider,
                source_filename=source_filename,
                page_count=page_count,
                snippet=snippets_by_uuid.get(uuid, ""),
            )
            for uuid, created, model, provider, source_filename, page_count in rows
        ]

    def _build_snippets_batch(self, session_uuids: list[str]) -> dict[str, str]:
        if not session_uuids:
            return {}
        placeholders = _placeholders(len(session_uuids))
        rows = self._conn.execute(
            f"SELECT session_uuid, content FROM snippets WHERE session_uuid IN ({placeholders})",
            session_uuids,
        ).fetchall()
        return {session_uuid: content for session_uuid, content in rows}
