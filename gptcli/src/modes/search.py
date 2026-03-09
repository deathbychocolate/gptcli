"""Interactive full-text search TUI over local chat and OCR history."""

import re
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

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
from gptcli.src.common.fts import (
    ChatFTS,
    MessageSnippet,
    OcrFTS,
    OcrHit,
    SessionHit,
    _BaseFTS,
    tokenize,
)

_RESULTS_HEIGHT = 14
_FOOTER_TEXT = " [↑↓/PgUp/PgDn] Navigate   [Enter] Load   [^P] Print   [^U] Clear   [ESC] Quit "
_OCR_FOOTER_TEXT = " [↑↓/PgUp/PgDn] Navigate   [Enter] Print   [^W] Write   [^U] Clear   [ESC] Quit "
_STYLE = Style.from_dict({"search-prefix": "bold"})
_LABEL_WIDTH = len("Assistant")
_SELECTED_GUTTER_STYLE = "fg:ansibrightcyan bold"
_OCR_ACCENT_STYLE = "fg:ansibrightblue bold"
_OCR_DOC_LABEL = "Doc:"

_T = TypeVar("_T")


class _BaseSearch(ABC, Generic[_T]):
    """Abstract base for full-text search TUI applications.

    Manages navigation state and shared TUI layout. Subclasses provide the FTS
    query, per-hit line count, hit rendering, footer text, and action key bindings.

    Attributes:
        _results: The current list of matching hits.
        _selected_idx: Index into _results of the highlighted row.
        _scroll_offset: Index of the first result rendered in the viewport.
        _action: The action chosen by the user (e.g. 'load', 'print', 'write', or None).
        _selected_uuid: The UUID of the session the user acted on.
        _cache_key: Identifies the last rendered state for fragment caching.
        _cached_fragments: Cached StyleAndTextTuples from the last render.
        _query_tokens: Lowercase alphanumeric tokens from the current query, for highlight logic.
        _highlight_pattern: Compiled regex built from _query_tokens, or None when no query.
        _total: Total number of sessions in the index.
        _total_width: Digit width of _total, for fixed-width counter formatting.
    """

    def __init__(self, fts: _BaseFTS[_T], total: int) -> None:
        """Initialise shared search state from a pre-built FTS index.

        Args:
            fts (_BaseFTS[_T]): The pre-built full-text search index.
            total (int): Total number of sessions in the index.
        """
        self._fts = fts
        self._results: list[_T] = []
        self._selected_idx: int = 0
        self._scroll_offset: int = 0
        self._action: str | None = None
        self._selected_uuid: str | None = None
        self._cache_key: tuple[int, int, int, tuple[str, ...]] | None = None
        self._cached_fragments: StyleAndTextTuples = []
        self._query_tokens: list[str] = []
        self._highlight_pattern: re.Pattern[str] | None = None
        self._total: int = total
        self._total_width: int = len(str(total))

    def _query(self, text: str) -> list[_T]:
        """Search the FTS index and return matching hits."""
        return self._fts.search(text)

    @abstractmethod
    def _lines_for(self, hit: _T) -> int:
        """Return the number of terminal lines this hit occupies in the viewport."""
        ...

    @abstractmethod
    def _render_hit_fragments(
        self, idx: int, hit: _T, is_selected: bool, pattern: re.Pattern[str] | None
    ) -> StyleAndTextTuples:
        """Render a single hit as styled text fragments."""
        ...

    @abstractmethod
    def _footer_text(self) -> str:
        """Return the footer help text shown at the bottom of the TUI."""
        ...

    @abstractmethod
    def _add_action_bindings(self, kb: KeyBindings, search_buffer: Buffer) -> None:
        """Register action key bindings (enter, ctrl+P, ctrl+W, etc.) onto kb."""
        ...

    def run(self) -> tuple[str | None, str | None]:
        """Build and run the prompt_toolkit search application.

        Returns:
            tuple[str | None, str | None]: A tuple of (action, session_uuid) where
                action is the chosen action string or None, and session_uuid is the
                selected session UUID or None if the user exited without selecting.
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
                        content=FormattedTextControl(lambda: self._footer_text(), focusable=False),
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
            self._results = self._query(search_buffer.text)
            self._query_tokens = tokenize(search_buffer.text)
            self._highlight_pattern = (
                re.compile("|".join(re.escape(t) for t in self._query_tokens), re.IGNORECASE)
                if self._query_tokens
                else None
            )
            self._selected_idx = 0
            self._scroll_offset = 0
            app.invalidate()

        search_buffer.on_text_changed += _on_query_changed

        self._results = self._query("")

        app.run()

        return self._action, self._selected_uuid

    # ── Internal helpers ────────────────────────────────────────────────

    def _build_key_bindings(self, search_buffer: Buffer) -> KeyBindings:
        """Build navigation key bindings shared by all search TUIs.

        Subclasses extend these by implementing _add_action_bindings.

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

        @kb.add("c-u")  # type: ignore[misc]
        def _clear(event: Any) -> None:
            search_buffer.reset()
            self._results = self._query("")
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

        self._add_action_bindings(kb, search_buffer)

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
                lines += self._lines_for(self._results[i])
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
            lines += self._lines_for(self._results[i])
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
                hit_lines = self._lines_for(hit)
                if lines_used + hit_lines > _RESULTS_HEIGHT:
                    break
                fragments += self._render_hit_fragments(idx, hit, idx == self._selected_idx, self._highlight_pattern)
                lines_used += hit_lines
                last_rendered = idx
            if last_rendered < len(self._results) - 1:
                fragments.append(("fg:ansigray", "  ↓ more…\n"))

        self._cache_key = cache_key
        self._cached_fragments = fragments
        return fragments


class ChatSearch(_BaseSearch[SessionHit]):
    """Interactive TUI for full-text search over chat history.

    Builds a ChatFTS index on initialisation, then runs a prompt_toolkit
    Application that updates results on every keystroke.
    """

    def __init__(self, chat_dir: str, encryption: Encryption | None) -> None:
        """Build the chat FTS index and initialise search state.

        Args:
            chat_dir (str): Path to the provider's chat storage directory.
            encryption (Encryption | None): Encryption instance, or None.
        """
        print(f"{GRN}>>>{RST} Indexing chat history…", end="\r", flush=True)
        fts = ChatFTS()
        total = fts.build(storage_dir=chat_dir, encryption=encryption)
        print(" " * 40, end="\r", flush=True)
        super().__init__(fts, total)

    def _lines_for(self, hit: SessionHit) -> int:
        return 2 + len(hit.snippets)

    def _render_hit_fragments(
        self, idx: int, hit: SessionHit, is_selected: bool, pattern: re.Pattern[str] | None
    ) -> StyleAndTextTuples:
        return _render_hit(idx, hit, is_selected, pattern)

    def _footer_text(self) -> str:
        return _FOOTER_TEXT

    def _add_action_bindings(self, kb: KeyBindings, search_buffer: Buffer) -> None:
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


class OcrSearch(_BaseSearch[OcrHit]):
    """Interactive TUI for full-text search over OCR history.

    Builds an OcrFTS index on initialisation, then runs a prompt_toolkit
    Application that updates results on every keystroke.
    """

    def __init__(self, ocr_dir: str, encryption: Encryption | None) -> None:
        """Build the OCR FTS index and initialise search state.

        Args:
            ocr_dir (str): Path to the provider's OCR storage directory.
            encryption (Encryption | None): Encryption instance, or None.
        """
        print(f"{GRN}>>>{RST} Indexing OCR history…", end="\r", flush=True)
        fts = OcrFTS()
        total = fts.build(storage_dir=ocr_dir, encryption=encryption)
        print(" " * 40, end="\r", flush=True)
        super().__init__(fts, total)

    def _lines_for(self, hit: OcrHit) -> int:
        return 2

    def _render_hit_fragments(
        self, idx: int, hit: OcrHit, is_selected: bool, pattern: re.Pattern[str] | None
    ) -> StyleAndTextTuples:
        return _render_ocr_hit(idx, hit, is_selected, pattern)

    def _footer_text(self) -> str:
        return _OCR_FOOTER_TEXT

    def _add_action_bindings(self, kb: KeyBindings, search_buffer: Buffer) -> None:
        @kb.add("enter")  # type: ignore[misc]
        def _print(event: Any) -> None:
            if self._results:
                self._action = SearchActions.PRINT.value
                self._selected_uuid = self._results[self._selected_idx].uuid
                event.app.exit()

        @kb.add("c-w")  # type: ignore[misc]
        def _write(event: Any) -> None:
            if self._results:
                self._action = SearchActions.WRITE.value
                self._selected_uuid = self._results[self._selected_idx].uuid
                event.app.exit()


def _render_ocr_hit(idx: int, hit: OcrHit, is_selected: bool, pattern: re.Pattern[str] | None) -> StyleAndTextTuples:
    """Render a single OCR search result as formatted text fragments.

    Args:
        idx (int): Zero-based index of this result in the list.
        hit (OcrHit): The search result to render.
        is_selected (bool): Whether this row is currently selected.
        pattern (re.Pattern[str] | None): Compiled highlight pattern for snippets.

    Returns:
        StyleAndTextTuples: Formatted text fragments for this result.
    """
    fragments: StyleAndTextTuples = []
    page_str = f"{hit.page_count} page{'s' if hit.page_count != 1 else ''}"

    if is_selected:
        fragments.append((_SELECTED_GUTTER_STYLE, f" [{idx + 1}] ▶ "))
        fragments.append(("bold", hit.created_display))
        fragments.append((_OCR_ACCENT_STYLE, f"  {hit.model or '?'}"))
        fragments.append(("fg:ansigray", f"  {page_str}"))
        fragments.append(("bold", f"  {hit.source_filename or '?'}\n"))
    else:
        fragments.append(("fg:ansigray", f" [{idx + 1}]   "))
        fragments.append(("bold", hit.created_display))
        fragments.append(("fg:ansigray", f"  {hit.model or '?'}  {page_str}  {hit.source_filename or '?'}\n"))

    if hit.snippet:
        fragments.append(("", "       "))
        fragments.append((_OCR_ACCENT_STYLE, _OCR_DOC_LABEL))
        fragments.append(("", "  "))
        fragments += _highlight_content(hit.snippet, pattern)
        fragments.append(("", "\n"))
    else:
        fragments.append(("", "\n"))

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
    label: str = ""
    role_style: str = ""
    match snippet.role.lower():
        case "user":
            label = snippet.role.title()
            role_style = "fg:ansibrightgreen bold"
        case "assistant":
            label = snippet.role.title()
            role_style = "fg:ansimagenta bold"
        case "system":
            label = snippet.role.title()
            role_style = "fg:ansibrightblue bold"
        case "developer":
            label = snippet.role.title()
            role_style = "fg:ansibrightblue bold"
        case _:
            label = snippet.role.title()
            role_style = "fg:ansigray bold"

    # add colon and padding
    label_colon = label + ":"
    padding = " " * max(0, _LABEL_WIDTH + 1 - len(label))

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
