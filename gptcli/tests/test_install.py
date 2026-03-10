"""Holds tests for the provider installer in install.py."""

import os


class TestProviderInstaller:

    class TestIsAlreadyInstalled:

        def test_returns_true_when_marker_exists(self, tmp_path: str) -> None:
            from gptcli.src.install import ProviderInstaller

            marker = os.path.join(str(tmp_path), ".install_successful")
            with open(marker, "w") as f:
                f.write("")
            installer = ProviderInstaller(
                provider="test",
                storage_dirs=[],
                keys_dir=str(tmp_path),
                key_file=os.path.join(str(tmp_path), "key"),
                install_marker=marker,
                api_provider="test",
                default_model="model",
                default_role="role",
                message_factory=None,  # type: ignore[arg-type]
            )
            assert installer._is_already_installed() is True

        def test_returns_false_when_marker_missing(self, tmp_path: str) -> None:
            from gptcli.src.install import ProviderInstaller

            marker = os.path.join(str(tmp_path), ".install_successful")
            installer = ProviderInstaller(
                provider="test",
                storage_dirs=[],
                keys_dir=str(tmp_path),
                key_file=os.path.join(str(tmp_path), "key"),
                install_marker=marker,
                api_provider="test",
                default_model="model",
                default_role="role",
                message_factory=None,  # type: ignore[arg-type]
            )
            assert installer._is_already_installed() is False
