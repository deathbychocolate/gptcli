"""SQLite FTS5-backed full-text search index for chat sessions."""

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from os import path
from typing import Any

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


class ChatFTS:
    """SQLite FTS5-backed full-text search over chat sessions.

    When encryption is disabled a persistent ``search.db`` file is kept
    alongside the chat sessions and updated incrementally — only new
    sessions are indexed on each launch.

    When encryption is enabled an in-memory database is used so that
    decrypted content is never written to disk.
    """

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    def build(self, chat_dir: str, encryption: Encryption | None) -> int:
        """Build or incrementally update the FTS index.

        Args:
            chat_dir (str): Path to the provider's chat storage directory.
            encryption (Encryption | None): Encryption instance or None.

        Returns:
            int: Total number of sessions in the index after building.
        """
        in_memory = encryption is not None
        db_path = ":memory:" if in_memory else path.join(chat_dir, _DB_FILENAME)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_schema()

        manifest = self._load_manifest(chat_dir, encryption)

        if in_memory:
            return self._full_build(chat_dir, manifest, encryption)
        return self._incremental_build(chat_dir, manifest, encryption)

    def search(self, query: str) -> list[SessionHit]:
        """Search sessions using FTS5 BM25 ranking, or return recent sessions for an empty query.

        Args:
            query (str): The search query string. Empty string returns the most recent sessions.

        Returns:
            list[SessionHit]: Up to 50 matching sessions ordered by relevance (or recency if no query).
        """
        if self._conn is None:
            return []

        if not query.strip():
            return self._all_sessions()

        tokens = self._tokenize(query)
        if not tokens:
            return []

        try:
            rows = self._conn.execute(
                """
                SELECT s.uuid, s.created, s.model, s.provider, s.message_count
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

    def _all_sessions(self) -> list[SessionHit]:
        # No LIMIT here by design: empty query means "browse full history",
        # whereas a typed query is capped at _MAX_RESULTS by BM25 relevance.
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT uuid, created, model, provider, message_count FROM sessions ORDER BY created DESC",
        ).fetchall()
        return self._build_hits(rows)

    def _build_hits(self, rows: list[tuple[str, float, str, str, int]]) -> list[SessionHit]:
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

    # ── Schema ───────────────────────────────────────────────────────

    def _create_schema(self) -> None:
        assert self._conn is not None
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

    # ── Build strategies ─────────────────────────────────────────────

    def _full_build(self, chat_dir: str, manifest: list[dict[str, Any]], encryption: Encryption | None) -> int:
        count = sum(1 for entry in manifest if self._index_session(chat_dir, entry, encryption))
        assert self._conn is not None
        self._conn.commit()
        return count

    def _incremental_build(self, chat_dir: str, manifest: list[dict[str, Any]], encryption: Encryption | None) -> int:
        assert self._conn is not None

        manifest_uuids = {e["uuid"] for e in manifest if "uuid" in e}
        existing_uuids = {row[0] for row in self._conn.execute("SELECT uuid FROM sessions")}

        to_delete = existing_uuids - manifest_uuids
        if to_delete:
            placeholders = self._placeholders(len(to_delete))
            args = list(to_delete)
            self._conn.execute(f"DELETE FROM sessions WHERE uuid IN ({placeholders})", args)
            self._conn.execute(f"DELETE FROM sessions_fts WHERE uuid IN ({placeholders})", args)
            self._conn.execute(f"DELETE FROM messages WHERE session_uuid IN ({placeholders})", args)

        to_add = [e for e in manifest if e.get("uuid") not in existing_uuids]
        added = sum(1 for entry in to_add if self._index_session(chat_dir, entry, encryption))

        self._conn.commit()
        return len(existing_uuids) - len(to_delete) + added

    def _index_session(self, chat_dir: str, entry: dict[str, Any], encryption: Encryption | None) -> bool:
        session_uuid = entry.get("uuid", "")
        created = float(entry.get("created", 0.0))
        if not session_uuid:
            return False

        session_dir = path.join(chat_dir, session_uuid)
        if not os.path.isdir(session_dir):
            return False

        messages = self._load_messages(session_dir, encryption)
        if messages is None:
            return False

        metadata = self._load_metadata(session_dir, encryption)
        model = metadata.get("chat", {}).get("model", "") if metadata else ""
        provider = metadata.get("chat", {}).get("provider", "") if metadata else ""

        content = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))

        assert self._conn is not None
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

    # ── Snippet extraction ───────────────────────────────────────────

    def _build_snippets_batch(self, session_uuids: list[str]) -> dict[str, list[MessageSnippet]]:
        assert self._conn is not None
        if not session_uuids:
            return {}
        placeholders = self._placeholders(len(session_uuids))
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
    def _placeholders(n: int) -> str:
        return ",".join("?" * n)

    # ── Helpers ──────────────────────────────────────────────────────

    def _load_manifest(self, chat_dir: str, encryption: Encryption | None) -> list[dict[str, Any]]:
        raw = read_text_file(path.join(chat_dir, GPTCLI_MANIFEST_FILENAME), encryption)
        if raw is None:
            return []
        try:
            result: list[dict[str, Any]] = json.loads(raw)
            return result
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text into lowercase alphanumeric tokens.

        Args:
            text (str): The text to tokenize.

        Returns:
            list[str]: A list of lowercase alphanumeric tokens.
        """
        return re.findall(r"[a-z0-9]+", text.lower())

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

    @staticmethod
    def _load_metadata(session_dir: str, encryption: Encryption | None) -> dict[str, Any] | None:
        raw = read_text_file(path.join(session_dir, GPTCLI_METADATA_FILENAME), encryption)
        if raw is None:
            return None
        try:
            metadata: dict[str, Any] = json.loads(raw)
            return metadata
        except json.JSONDecodeError:
            return None
