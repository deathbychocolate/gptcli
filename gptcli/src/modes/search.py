"""Interactive full-text search TUI over local chat history."""

import re
from typing import Any

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import AnyFormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.styles import Style

from gptcli.src.common.constants import GRN, RST, SearchActions
from gptcli.src.common.encryption import Encryption
from gptcli.src.common.fts import ChatFTS, MessageSnippet, SessionHit

_RESULTS_HEIGHT = 14
_FOOTER_TEXT = " [↑↓/PgUp/PgDn] Navigate   [Enter] Load   [^P] Print   [^U] Clear   [ESC] Quit "
_STYLE = Style.from_dict({"search-prefix": "bold"})
_LABEL_WIDTH = len("Assistant")
_SELECTED_GUTTER_STYLE = "fg:ansibrightcyan bold"


class ChatSearch:
    """Interactive TUI for full-text search over chat history.

    Builds a ChatFTS index on initialisation, then runs a prompt_toolkit
    Application that updates results on every keystroke.

    Attributes:
        _fts: The full-text search index.
        _total: Total number of sessions in the index.
        _total_width: Digit width of _total, for fixed-width counter formatting.
        _results: The current list of matching SessionHit objects.
        _selected_idx: Index into _results of the highlighted row.
        _scroll_offset: Index of the first result rendered in the viewport.
        _action: The action chosen by the user ('load', 'print', or None).
        _selected_uuid: The UUID of the session the user acted on.
        _cache_key: Identifies the last rendered state for fragment caching.
        _cached_fragments: Cached StyleAndTextTuples from the last render.
        _query_tokens: Lowercase alphanumeric tokens from the current query, for highlight logic.
        _highlight_pattern: Compiled regex built from _query_tokens, or None when no query.
    """

    def __init__(self, chat_dir: str, encryption: Encryption | None) -> None:
        """Build the FTS index and prepare the TUI state.

        Args:
            chat_dir (str): Path to the provider's chat storage directory.
            encryption (Encryption | None): Encryption instance, or None.
        """
        self._results: list[SessionHit] = []
        self._selected_idx: int = 0
        self._scroll_offset: int = 0
        self._action: str | None = None
        self._selected_uuid: str | None = None
        self._cache_key: tuple[int, int, int, tuple[str, ...]] | None = None
        self._cached_fragments: StyleAndTextTuples = []
        self._query_tokens: list[str] = []
        self._highlight_pattern: re.Pattern[str] | None = None

        print(f"{GRN}>>>{RST} Indexing chat history…", end="\r", flush=True)
        self._fts = ChatFTS()
        self._total: int = self._fts.build(chat_dir=chat_dir, encryption=encryption)
        self._total_width: int = len(str(self._total))
        print(" " * 40, end="\r", flush=True)  # clear the indexing line

    def run(self) -> tuple[str | None, str | None]:
        """Build and run the prompt_toolkit search application.

        Returns:
            tuple[str | None, str | None]: A tuple of (action, session_uuid) where
                action is 'load', 'print', or None, and session_uuid is the selected
                session UUID or None if the user exited without selecting.
        """
        search_buffer = Buffer(name="search")
        kb = self._build_key_bindings(search_buffer)

        layout = Layout(
            HSplit(
                [
                    Window(
                        content=BufferControl(buffer=search_buffer, focusable=True),
                        height=1,
                        get_line_prefix=self._search_line_prefix,
                    ),
                    Window(height=1, char="─"),
                    Window(
                        content=FormattedTextControl(self._get_results_text, focusable=False),
                        height=_RESULTS_HEIGHT,
                    ),
                    Window(height=1, char="─"),
                    Window(
                        content=FormattedTextControl(lambda: _FOOTER_TEXT, focusable=False),
                        height=1,
                    ),
                ]
            ),
            focused_element=search_buffer,
        )

        app: Application[Any] = Application(
            layout=layout,
            key_bindings=kb,
            style=_STYLE,
            full_screen=False,
            mouse_support=False,
        )

        def _on_query_changed(_: Buffer) -> None:
            self._results = self._fts.search(search_buffer.text)
            self._query_tokens = ChatFTS._tokenize(search_buffer.text)
            self._highlight_pattern = (
                re.compile("|".join(re.escape(t) for t in self._query_tokens), re.IGNORECASE)
                if self._query_tokens
                else None
            )
            self._selected_idx = 0
            self._scroll_offset = 0
            app.invalidate()

        search_buffer.on_text_changed += _on_query_changed

        self._results = self._fts.search("")

        app.run()

        return self._action, self._selected_uuid

    # ── Internal helpers ────────────────────────────────────────────────

    def _build_key_bindings(self, search_buffer: Buffer) -> KeyBindings:
        """Build key bindings for navigation and actions.

        Args:
            search_buffer (Buffer): The search input buffer, needed for Ctrl+U.

        Returns:
            KeyBindings: Configured key bindings for the search TUI.
        """
        kb = KeyBindings()

        @kb.add("escape", eager=True)  # type: ignore[misc]
        def _exit(event: Any) -> None:
            event.app.exit()

        @kb.add("up")  # type: ignore[misc]
        def _up(event: Any) -> None:
            if self._selected_idx > 0:
                self._selected_idx -= 1
                self._clamp_scroll()
                event.app.invalidate()

        @kb.add("down")  # type: ignore[misc]
        def _down(event: Any) -> None:
            if self._selected_idx < len(self._results) - 1:
                self._selected_idx += 1
                self._clamp_scroll()
                event.app.invalidate()

        @kb.add("enter")  # type: ignore[misc]
        def _load(event: Any) -> None:
            if self._results:
                self._action = SearchActions.LOAD.value
                self._selected_uuid = self._results[self._selected_idx].uuid
                event.app.exit()

        @kb.add("c-p")  # type: ignore[misc]
        def _print(event: Any) -> None:
            if self._results:
                self._action = SearchActions.PRINT.value
                self._selected_uuid = self._results[self._selected_idx].uuid
                event.app.exit()

        @kb.add("c-u")  # type: ignore[misc]
        def _clear(event: Any) -> None:
            search_buffer.reset()
            self._results = self._fts.search("")
            self._query_tokens = []
            self._highlight_pattern = None
            self._selected_idx = 0
            self._scroll_offset = 0
            event.app.invalidate()

        @kb.add("pageup")  # type: ignore[misc]
        def _page_up(event: Any) -> None:
            if self._selected_idx > 0:
                self._selected_idx = max(0, self._selected_idx - self._page_size())
                self._clamp_scroll()
                event.app.invalidate()

        @kb.add("pagedown")  # type: ignore[misc]
        def _page_down(event: Any) -> None:
            if self._selected_idx < len(self._results) - 1:
                self._selected_idx = min(len(self._results) - 1, self._selected_idx + self._page_size())
                self._clamp_scroll()
                event.app.invalidate()

        return kb

    def _clamp_scroll(self) -> None:
        """Adjust _scroll_offset so that _selected_idx is visible in the viewport.

        Scrolls up instantly when selected moves above the viewport.
        Scrolls down one step at a time until the selected item fits within
        _RESULTS_HEIGHT lines.
        """
        if self._selected_idx < self._scroll_offset:
            self._scroll_offset = self._selected_idx
            return

        while self._scroll_offset < self._selected_idx:
            lines = 0
            for i in range(self._scroll_offset, len(self._results)):
                lines += 2 + len(self._results[i].snippets)  # header + snippets + blank
                if i == self._selected_idx:
                    if lines <= _RESULTS_HEIGHT:
                        return  # selected fits — done
                    break  # selected overflows — advance offset
                if lines >= _RESULTS_HEIGHT:
                    break  # selected not reached — advance offset
            self._scroll_offset += 1

    def _page_size(self) -> int:
        """Compute how many results fit in the viewport from the current scroll offset.

        Returns:
            int: Number of results that fit, at least 1.
        """
        lines = 0
        count = 0
        for i in range(self._scroll_offset, len(self._results)):
            lines += 2 + len(self._results[i].snippets)
            if lines > _RESULTS_HEIGHT:
                break
            count += 1
        return max(1, count)

    def _search_line_prefix(self, _line_number: int, _wrap_count: int) -> AnyFormattedText:
        """Return the prefix shown before the search input, including result count.

        Args:
            _line_number (int): Unused — required by prompt_toolkit API.
            _wrap_count (int): Unused — required by prompt_toolkit API.

        Returns:
            AnyFormattedText: The formatted prefix text.
        """
        return [
            ("class:search-prefix", f" Search [{len(self._results):>{self._total_width}}/{self._total}]: "),
        ]

    def _get_results_text(self) -> StyleAndTextTuples:
        """Render the visible slice of results as formatted text.

        Caches rendered fragments by (results identity, selected index, scroll
        offset, query tokens) to avoid redundant work when prompt_toolkit calls
        this function multiple times per render cycle.

        Returns:
            StyleAndTextTuples: A list of (style, text) pairs for rendering.
        """
        cache_key = (id(self._results), self._selected_idx, self._scroll_offset, tuple(self._query_tokens))
        if cache_key == self._cache_key:
            return self._cached_fragments

        if not self._results:
            fragments: StyleAndTextTuples = [("fg:ansigray", "  No results.\n")]
        else:
            fragments = []
            lines_used = 0
            last_rendered = self._scroll_offset - 1
            for idx in range(self._scroll_offset, len(self._results)):
                hit = self._results[idx]
                hit_lines = 2 + len(hit.snippets)  # header + snippets + blank
                if lines_used + hit_lines > _RESULTS_HEIGHT:
                    break
                fragments += _render_hit(idx, hit, idx == self._selected_idx, self._highlight_pattern)
                lines_used += hit_lines
                last_rendered = idx
            if last_rendered < len(self._results) - 1:
                fragments.append(("fg:ansigray", "  ↓ more…\n"))

        self._cache_key = cache_key
        self._cached_fragments = fragments
        return fragments


def _highlight_content(content: str, pattern: re.Pattern[str] | None) -> StyleAndTextTuples:
    """Return formatted text fragments with query tokens highlighted in yellow.

    Args:
        content (str): The text to highlight.
        pattern (re.Pattern[str] | None): Compiled highlight pattern, or None for no highlighting.

    Returns:
        StyleAndTextTuples: Fragments with matched spans styled in bold yellow.
    """
    if pattern is None:
        return [("", content)]
    fragments: StyleAndTextTuples = []
    pos = 0
    for m in pattern.finditer(content):
        if pos < m.start():
            fragments.append(("", content[pos : m.start()]))
        fragments.append(("fg:ansiyellow bold", content[m.start() : m.end()]))
        pos = m.end()
    if pos < len(content):
        fragments.append(("", content[pos:]))
    return fragments


def _render_hit(idx: int, hit: SessionHit, is_selected: bool, pattern: re.Pattern[str] | None) -> StyleAndTextTuples:
    """Render a single search result as formatted text fragments.

    Args:
        idx (int): Zero-based index of this result in the list.
        hit (SessionHit): The search result to render.
        is_selected (bool): Whether this row is currently selected.
        pattern (re.Pattern[str] | None): Compiled highlight pattern for snippets.

    Returns:
        StyleAndTextTuples: Formatted text fragments for this result.
    """
    fragments: StyleAndTextTuples = []
    meta = f"  {hit.model or '?'}  {hit.message_count} msg\n"

    if is_selected:
        fragments.append((_SELECTED_GUTTER_STYLE, f" [{idx + 1}] ▶ "))
        fragments.append(("bold", hit.created_display))
        fragments.append(("", meta))
    else:
        fragments.append(("fg:ansigray", f" [{idx + 1}]   "))
        fragments.append(("bold", hit.created_display))
        fragments.append(("fg:ansigray", meta))

    for snippet in hit.snippets:
        fragments += _render_snippet(snippet, pattern)

    fragments.append(("", "\n"))
    return fragments


def _snippet_label(snippet: MessageSnippet) -> tuple[str, str, str]:
    """Return (label_colon, padding, role_style) for a snippet's role label.

    Args:
        snippet (MessageSnippet): The snippet whose role label to derive.

    Returns:
        tuple[str, str, str]: label+colon, alignment padding, and the colour style string.
    """
    is_user = "user" in snippet.role.lower()
    label = "User" if is_user else "Assistant"
    label_colon = label + ":"
    padding = " " * (_LABEL_WIDTH + 1 - len(label))
    role_style = "fg:ansibrightgreen bold" if is_user else "fg:ansimagenta bold"
    return label_colon, padding, role_style


def _render_snippet(snippet: MessageSnippet, pattern: re.Pattern[str] | None) -> StyleAndTextTuples:
    """Render a message snippet with colour-coded role label and highlighted query terms.

    Args:
        snippet (MessageSnippet): The snippet to render.
        pattern (re.Pattern[str] | None): Compiled highlight pattern, or None for no highlighting.

    Returns:
        StyleAndTextTuples: Formatted text fragments for this snippet.
    """
    label_colon, padding, role_style = _snippet_label(snippet)
    return [
        ("", "       "),
        (role_style, label_colon),
        ("", padding),
        *_highlight_content(snippet.content, pattern),
        ("", "\n"),
    ]
