"""Shared test configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _fast_scrypt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reduce scrypt cost parameter for faster test execution."""
    monkeypatch.setattr("gptcli.src.common.encryption._SCRYPT_N", 2**10)
    monkeypatch.setattr("gptcli.src.common.key_management._SCRYPT_N", 2**10)
