"""Holds all the tests for nuke.py."""

import os
from unittest.mock import patch

from gptcli.src.cli import CommandParser
from gptcli.src.modes.nuke import Nuke


class TestNuke:

    class TestNukeMethod:

        def test_deletes_root_directory(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(os.path.join(root, "subdir"))
            with open(os.path.join(root, "subdir", "file.json"), "w") as f:
                f.write("data")

            with patch("builtins.input", return_value="yes"):
                Nuke.nuke(root_dir=root)

            assert not os.path.exists(root)

        def test_returns_true_on_success(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(root)

            with patch("builtins.input", return_value="yes"):
                result = Nuke.nuke(root_dir=root)

            assert result is True

        def test_returns_false_on_user_abort(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(root)

            with patch("builtins.input", return_value="no"):
                result = Nuke.nuke(root_dir=root)

            assert result is False
            assert os.path.isdir(root)

        def test_returns_false_when_directory_missing(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "nonexistent")

            result = Nuke.nuke(root_dir=root)

            assert result is False

        def test_returns_false_on_keyboard_interrupt(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(root)

            with patch("builtins.input", side_effect=KeyboardInterrupt):
                result = Nuke.nuke(root_dir=root)

            assert result is False
            assert os.path.isdir(root)

        def test_returns_false_on_os_error(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(root)

            with patch("builtins.input", return_value="yes"):
                with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
                    result = Nuke.nuke(root_dir=root)

            assert result is False

        def test_returns_false_on_eof(self, tmp_path: str) -> None:
            root = os.path.join(str(tmp_path), "gptcli_data")
            os.makedirs(root)

            with patch("builtins.input", side_effect=EOFError):
                result = Nuke.nuke(root_dir=root)

            assert result is False
            assert os.path.isdir(root)

    class TestCliRouting:

        def test_nuke_command_parsed_for_all(self) -> None:
            with patch("sys.argv", ["gptcli", "all", "nuke"]):
                parser = CommandParser()
                parser.configure_command_parser()

            assert parser.args.provider == "all"
            assert parser.args.mode_name == "nuke"
