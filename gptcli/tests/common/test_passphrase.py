"""Holds all the tests for passphrase.py."""

from unittest.mock import patch

from gptcli.src.common.passphrase import (
    _MAX_RETRIES,
    _MIN_LENGTH,
    PassphrasePrompt,
)


class TestPassphrasePrompt:

    class TestPrompt:

        def test_returns_none_on_keyboard_interrupt(self) -> None:
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=KeyboardInterrupt):
                assert PassphrasePrompt.prompt("Enter passphrase: ") is None

        def test_returns_none_on_eof_error(self) -> None:
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=EOFError):
                assert PassphrasePrompt.prompt("Enter passphrase: ") is None

        def test_returns_none_on_unexpected_exception(self) -> None:
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=RuntimeError):
                assert PassphrasePrompt.prompt("Enter passphrase: ") is None

        def test_returns_input_on_success(self) -> None:
            with patch("gptcli.src.common.passphrase.getpass.getpass", return_value="my-passphrase"):
                assert PassphrasePrompt.prompt("Enter passphrase: ") == "my-passphrase"

    class TestCreateWithConfirmation:

        def test_matching_passphrases_returns_passphrase(self) -> None:
            passphrase = "my-secure-pass-1234"
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=[passphrase, passphrase]):
                result = PassphrasePrompt.create_with_confirmation()
            assert result == passphrase

        def test_mismatched_then_matching_passphrases_succeeds(self) -> None:
            good = "correct-passphrase!"
            with patch(
                "gptcli.src.common.passphrase.getpass.getpass",
                side_effect=["first-pass-long-xx", "second-pass-long-x", good, good],
            ):
                result = PassphrasePrompt.create_with_confirmation()
            assert result == good

        def test_returns_none_after_max_retries(self) -> None:
            mismatches: list[str] = []
            for i in range(_MAX_RETRIES):
                mismatches.extend([f"passphrase-long-{i}a", f"passphrase-long-{i}b"])
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=mismatches):
                assert PassphrasePrompt.create_with_confirmation() is None

        def test_returns_none_when_prompt_aborted(self) -> None:
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=KeyboardInterrupt):
                assert PassphrasePrompt.create_with_confirmation() is None

        def test_short_passphrase_does_not_consume_confirmation_retries(self) -> None:
            short = "short"
            valid = "a" * _MIN_LENGTH
            with patch(
                "gptcli.src.common.passphrase.getpass.getpass",
                side_effect=[short, short, valid, valid],
            ):
                result = PassphrasePrompt.create_with_confirmation()
            assert result == valid

        def test_accepts_passphrase_at_minimum_length(self) -> None:
            passphrase = "a" * _MIN_LENGTH
            with patch("gptcli.src.common.passphrase.getpass.getpass", side_effect=[passphrase, passphrase]):
                result = PassphrasePrompt.create_with_confirmation()
            assert result == passphrase

    class TestPromptForValidPassphrase:

        def test_returns_passphrase_meeting_minimum_length(self) -> None:
            valid = "a" * _MIN_LENGTH
            with patch("gptcli.src.common.passphrase.getpass.getpass", return_value=valid):
                assert PassphrasePrompt._prompt_for_valid_passphrase("prompt: ") == valid

        def test_retries_until_valid_length_provided(self) -> None:
            short = "short"
            valid = "a" * _MIN_LENGTH
            with patch(
                "gptcli.src.common.passphrase.getpass.getpass",
                side_effect=[short, short, short, valid],
            ):
                assert PassphrasePrompt._prompt_for_valid_passphrase("prompt: ") == valid

        def test_accepts_passphrase_longer_than_minimum(self) -> None:
            long = "a" * (_MIN_LENGTH + 10)
            with patch("gptcli.src.common.passphrase.getpass.getpass", return_value=long):
                assert PassphrasePrompt._prompt_for_valid_passphrase("prompt: ") == long
