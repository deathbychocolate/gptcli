# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPTCLI is a Python CLI client for accessing LLM providers (OpenAI and Mistral AI) via their APIs. Published on PyPI as `dbc-gptcli`. Supports Python 3.11-3.14 on Linux and macOS.

**Entry Point:** `gptcli/main.py:main()` → installed as `gptcli` command
**Current Version:** 0.25.0

## Development Commands

### Initial Setup
```bash
make setup    # One-time: Install pre-commit hooks
make install  # Install dependencies and mypy types using uv
```

### Testing
```bash
make test           # Run pytest (stops on first failure, ERROR-level logs)
make test_nox       # Test on Python 3.11, 3.12, 3.13, 3.14 via nox
make coverage       # Generate HTML coverage report in htmlcov/
pytest path/to/test_file.py::test_name  # Run single test
```

### Code Quality
Pre-commit hooks run automatically on commit:
- **mypy** (strict): Type checking
- **autoflake**: Remove unused imports/variables
- **black** (line-length=120): Code formatting
- **isort** (line-length=120, black profile): Import sorting

Manual execution:
```bash
uv run mypy gptcli/
uv run black gptcli/
uv run isort gptcli/
```

### Build & Clean
```bash
make build           # Create wheel and tarball in dist/
make clean           # Remove __pycache__ and .cpython files
make clean_coverage  # Remove .coverage and htmlcov/
```

### Running the CLI
```bash
gptcli openai chat                    # Interactive chat mode
gptcli mistral se "Your message"      # Single exchange
gptcli mistral ocr file.pdf           # OCR mode (Mistral only)
gptcli [provider] [mode] --help       # Mode-specific help
```

## Architecture

### High-Level Flow
```
CLI Arguments (cli.py)
    ↓
main.py (validate, load API key, route to mode)
    ↓
Mode Class (chat.py, single_exchange.py, ocr.py)
    ↓
API Classes (Chat/SingleExchange in common/api.py)
    ↓
EndpointHelper (provider config, HTTP error handling)
    ↓
HTTP POST to Provider API
```

### Key Components

**1. Mode System** (`gptcli/src/modes/`)
- **Chat** (`chat.py`): Multi-turn conversations with prompt-toolkit, streaming, local storage, history navigation
- **SingleExchange** (`single_exchange.py`): One message → one reply → exit (automation-friendly)
- **OCR** (`optical_character_recognition.py`): Document-to-markdown conversion (Mistral only)
- **Search** (`search.py`): Interactive TUI (prompt-toolkit) for full-text search over chat and OCR history; `ChatSearch` and `OcrSearch` subclasses

**2. Provider Abstraction** (`gptcli/src/common/`)
- **api.py**: `EndpointHelper`, `Chat`, `SingleExchange` classes handle provider-specific endpoints, keys, message factories
- **message.py**: `Message` objects with provider-specific token counting (tiktoken for OpenAI, mistral-common for Mistral)
- **MessageFactory**: Creates provider-specific messages
- **constants.py**: Enums for models, roles, commands (e.g., `OpenaiModelsChat`, `MistralUserRoles`)

**3. Storage System** (`gptcli/src/common/storage.py`)
- JSON files in `~/.gptcli/[provider]/storage/json/`
- Format: `[epoch]_[datetime]_chat.json`
- "Last session" lookup uses epoch-prefix-based ordering (`max(..., key=basename)`) rather than filesystem timestamps
- Supports optional transparent encryption (`.enc` extension when enabled)
- Two representations:
  - **Reduced context** (API): role + content only (saves tokens)
  - **Full context** (storage): all metadata for reconstruction

**4. File Ingestion** (`gptcli/src/common/ingest.py`)
- Abstract `File` class with `Text` and `PDF` implementations
- Used for adding file context to messages

**5. Installation & Migration** (`gptcli/src/install.py`)
- `Migrate`: Handles version upgrades (0.20.2 → latest)
- Provider-specific installers create directory structure, prompt for API keys

**6. Input Validation** (`gptcli/src/common/validators.py`)
- Classifies inputs as `URL`, `FILEPATH`, or `UNSUPPORTED` via `classify_input()`
- Uses `validators` library for URL detection

**7. Encryption at Rest** (`gptcli/src/common/encryption.py`, `key_management.py`, `passphrase.py`)
- **Encryption**: AES-256-GCM encryption/decryption with scrypt key derivation (N=2^17)
- **KeyManager**: Key lifecycle with 12-hour session caching via wrapping key in volatile storage
- **PassphrasePrompt**: User passphrase input with 16-character minimum and confirmation
- Files: salt (`~/.gptcli/.salt`), verification token (`.verify.enc`), cached key (`.key`)

**8. Commands** (`gptcli/src/commands/`)
- **EncryptionCommands** (`encryption_commands.py`): Orchestrates batch encrypt/decrypt/rekey operations across providers; atomic 3-phase rekey: decrypt with old key → re-encrypt with new key → swap files → update key material
- **Nuke** (`nuke.py`): Permanently deletes the entire `~/.gptcli` directory after interactive confirmation

**9. Full-Text Search** (`gptcli/src/common/fts.py`)
- SQLite FTS5 index built on-demand from storage files
- `ChatFTS`: indexes message content across all chat sessions
- `OcrFTS`: indexes OCR Markdown output across all OCR sessions
- Returns ranked hits with snippets; max 50 results

### Provider Configuration

Both providers support:
- Chat and SingleExchange modes
- Streaming responses
- Local storage
- Context retention

**OpenAI**
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Default model: `gpt-5-mini`
- User roles: `platform`, `developer`, `guideline`, `user`
- Model roles: `assistant`

**Mistral**
- Chat endpoint: `https://api.mistral.ai/v1/chat/completions`
- OCR endpoint: `https://api.mistral.ai/v1/ocr`
- Default chat model: `mistral-large-latest`
- User roles: `user`
- Model roles: `assistant`, `function`, `system`, `tool`

### CLI Architecture (`gptcli/src/cli.py`)

Hierarchical argument parsing:
```
gptcli [--no-cache]
├── all
│   ├── encrypt
│   ├── decrypt
│   ├── rekey
│   └── nuke
├── mistral
│   ├── chat [--context] [--stream] [--store] [--load-last]
│   ├── se [--output plain|choices|all]
│   ├── ocr [--store] [--display-last] [--display] [--filelist] [--output-dir] [--no-output-dir] [--no-images]
│   └── search
│       ├── chat
│       └── ocr [--output-dir] [--no-output-dir]
└── openai
    ├── chat
    ├── se
    └── search
        └── chat
```

Common arguments added to all modes: `--model`, `--role-user`, `--role-model`, `--key`, `--filepath`
Global arguments: `--no-cache` (disables encryption key caching, prompts for passphrase every time)

## Important Patterns

### Error Handling
- **Decorators** (`common/decorators.py`):
  - `@user_triggered_abort`: Catches Ctrl+C/EOFError → sys.exit()
  - `@allow_graceful_stream_exit`: Catches errors during streaming
- **HTTP errors** in `EndpointHelper._check_for_http_errors()`: Handles 401, 404, 429, 503

### Code Style
- **Line length**: 120 characters (black, isort)
- **Type hints**: Required for all functions (mypy strict)
- **Enums**: Base class `BaseEnum` with `.to_list()` and `.default()` helpers
- **Factory pattern**: MessageFactory for provider-specific object creation
- **Imports**: Always at the top of the file with other imports, never inside functions or classes
- **Classes over functions**: Prefer classes and methods over standalone functions where it makes sense. Use `@staticmethod` for methods that don't access instance state
- **Readability**: Code must always be readable and express *what* it does, not the steps taken to achieve it. Name variables, methods, and classes to convey intent. If existing code needs refactoring to meet this standard, refactor it

### Docstrings
Use Google-style docstrings with explicit types in Args and Returns sections:
```python
def process_document(filepath: str, validate: bool) -> tuple[str, int]:
    """Brief description of what the function does.

    Args:
        filepath (str): Path to the document to process.
        validate (bool): Whether to validate the document before processing.

    Returns:
        tuple[str, int]: A tuple containing the processed content and page count.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If validation fails.
    """
```

### HTTP Requests
Prefer helper methods returning `Response | None` over nested try/except blocks:
```python
def _make_request(self, url: str, payload: dict) -> Response | None:
    """Make HTTP request, returning None on failure."""
    try:
        response = post(url=url, json=payload, timeout=30)
        return response if response.ok else None
    except RequestException:
        return None

def fetch_data(self, url: str) -> str:
    """Fetch data with fallback."""
    response = self._make_request(url, primary_payload)
    if response is None:
        response = self._make_request(url, fallback_payload)
    if response is None:
        raise RuntimeError("Request failed")
    return response.text
```
This keeps control flow linear and readable.

### Testing
- Mirror structure: `gptcli/tests/` matches `gptcli/src/`
- Session-scoped fixtures for setup/teardown
- Mock external dependencies (API calls)
- Coverage target via `make coverage`

**Test Class Structure**: Use nested classes to organize tests by method:
```python
class TestStorage:
    """Tests for the Storage class."""

    class TestStoreMessages:
        """Tests for Storage.store_messages()."""

        def test_creates_json_file(self) -> None:
            ...

        def test_raises_error_on_empty_messages(self) -> None:
            ...

    class TestExtractMessages:
        """Tests for Storage.extract_messages()."""

        def test_returns_messages_collection(self) -> None:
            ...
```

**Test Quality Guidelines**:
- Keep tests simple and maintainable by the average engineer
- Focus on high-value tests that verify important behavior
- Always cover edge cases (empty inputs, None values, boundary conditions)
- Avoid complex tests that don't check important functionality—simplify or replace with equivalent but clearer tests

### File Paths
- Constants in `gptcli/constants.py` define all storage paths
- Structure: `~/.gptcli/[provider]/[keys|storage]/...`
- Encryption files: `~/.gptcli/.salt`, `~/.gptcli/.key`, `~/.gptcli/.verify.enc`, `~/.gptcli/.kdf_params`
- Migration maintains backward compatibility

## Current Development State

### Fully Functional
- Chat mode (both providers)
- Single Exchange mode (both providers)
- Local storage (JSON)
- Streaming responses
- API key management
- File ingestion (text, PDF)
- OCR mode (Mistral only)
- Encryption at rest (AES-256-GCM with scrypt key derivation)
- Full Text Search for chat storage (both providers)
- Full Text Search for OCR results (Mistral only)
- Nuke command (permanent data deletion)

### In Development (TODOs in README)
- Additional role types (developer, tool, function)
- Database storage backend

### Known Issues
- OCR mode only supports Mistral (OpenAI not implemented)
- File ingestion incomplete in SingleExchange mode

## Extension Points

**Adding a new provider:**
1. Add to `ProviderNames` enum in `common/constants.py`
2. Create model/role enums (e.g., `NewProviderModelsChat`)
3. Update `EndpointHelper` to handle new provider
4. Add message factory logic for provider-specific messages
5. Update `main.py` installation routing

**Adding a new mode:**
1. Create mode class in `gptcli/src/modes/`
2. Register in `cli.py` (add subparser)
3. Add routing in `main.py` (match statement)
4. Implement mode-specific API class if needed

**Adding file type support:**
1. Extend `File` ABC in `common/ingest.py`
2. Implement `extract_text()` method
3. Add file type detection logic

## CI/CD Pipeline

GitHub Actions (`.github/workflows/main.yml`) runs on push/PR to main:

1. **Code Quality** (Ubuntu, Python 3.11): Pre-commit hooks
2. **Tests Matrix** (Linux + macOS × Python 3.11-3.14):
   - Install dependencies using uv
   - Run full pytest suite
   - Requires secrets: `DBC_GPTCLI_MISTRAL_API_KEY`, `DBC_GPTCLI_OPENAI_API_KEY`

**Release** (`.github/workflows/release.yml`) runs on push to main:

1. **Test**: Run pytest on Python 3.11
2. **Bump Version**: Auto-bump with commitizen (skips if commit is already a bump)
3. **Docker**: Build and push to Docker Hub (tagged with version + latest)
4. **PyPI**: Build and publish package via trusted publishing
- Requires additional secrets: `PAT_TOKEN`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

## Versioning

- **Tool**: commitizen (semantic versioning)
- **Version files**: `pyproject.toml`, `gptcli/_version.py`
- **Format**: `$version` (no prefix)
- **Changelog**: Auto-updated on version bump
- **Post-bump hook**: Updates version in `uv.lock` via `scripts/update_uv_lock_version.py`
