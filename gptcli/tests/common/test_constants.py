"""File that will hold all the tests relating to test_constants.py."""

import os

import pytest
import requests
from requests import Response

from gptcli.constants import (
    MISTRAL_API_KEY,
    MISTRAL_ENDPOINT_CHAT_COMPLETIONS,
    OPENAI_API_KEY,
    OPENAI_ENDPOINT_CHAT_COMPLETIONS,
)
from gptcli.src.common.constants import (
    ChatCommands,
    MistralModelsChat,
    MistralUserRoles,
    OpenaiModelsChat,
    OpenaiUserRoles,
    ProviderNames,
)


class TestMistralModelsChat:

    @pytest.mark.third_party_api
    @pytest.mark.parametrize("model", [class_var.value for class_var in MistralModelsChat])
    def test_should_successfully_send_a_message_to_the_api_given_a_valid_model(self, model: str) -> None:
        url: str = MISTRAL_ENDPOINT_CHAT_COMPLETIONS
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + os.environ[MISTRAL_API_KEY],
        }
        body = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": "Only show the number, which is bigger? 1 or 2?"}],
        }
        response: Response = requests.post(url=url, headers=headers, stream=False, json=body, timeout=30)
        assert response.status_code == 200, f"API request failed: {response.status_code} - {response.text}"

    class TestDefault:

        def test_should_return_str_type(self) -> None:
            assert isinstance(MistralModelsChat.default(), str)


class TestOpenaiModelsChat:

    @pytest.mark.third_party_api
    @pytest.mark.parametrize("model", [class_var.value for class_var in OpenaiModelsChat])
    def test_should_successfully_send_a_message_to_the_api_given_a_valid_model(self, model: str) -> None:
        url: str = OPENAI_ENDPOINT_CHAT_COMPLETIONS
        headers = {
            "Accept": "text/event-stream",
            "Authorization": "Bearer " + os.environ[OPENAI_API_KEY],
        }
        body = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": "Only show the number, which is bigger? 1 or 2?"}],
        }
        response: Response = requests.post(url=url, headers=headers, stream=False, json=body, timeout=30)
        assert response.status_code == 200, f"API request failed: {response.status_code} - {response.text}"

    class TestDefault:

        def test_should_return_str_type(self) -> None:
            assert isinstance(OpenaiModelsChat.default(), str)


class TestChatCommands:
    """Tests for ChatCommands system/developer command classmethods."""

    class TestSystem:
        """Tests for ChatCommands.system()."""

        def test_returns_sys_commands(self) -> None:
            result = ChatCommands.system()
            assert result == ["/sys", "/system"]

        def test_returns_list_of_strings(self) -> None:
            assert all(isinstance(cmd, str) for cmd in ChatCommands.system())

    class TestSystemClear:
        """Tests for ChatCommands.system_clear()."""

        def test_returns_sys_clear_command(self) -> None:
            result = ChatCommands.system_clear()
            assert result == ["/sys-clear"]

    class TestDeveloper:
        """Tests for ChatCommands.developer()."""

        def test_returns_dev_commands(self) -> None:
            result = ChatCommands.developer()
            assert result == ["/dev", "/developer"]

        def test_returns_list_of_strings(self) -> None:
            assert all(isinstance(cmd, str) for cmd in ChatCommands.developer())

    class TestDeveloperClear:
        """Tests for ChatCommands.developer_clear()."""

        def test_returns_dev_clear_command(self) -> None:
            result = ChatCommands.developer_clear()
            assert result == ["/dev-clear"]

    class TestSystemShow:
        """Tests for ChatCommands.system_show()."""

        def test_returns_sys_show_command(self) -> None:
            result = ChatCommands.system_show()
            assert result == ["/sys-show"]

    class TestDeveloperShow:
        """Tests for ChatCommands.developer_show()."""

        def test_returns_dev_show_command(self) -> None:
            result = ChatCommands.developer_show()
            assert result == ["/dev-show"]

    class TestHelpDoc:
        """Tests for ChatCommands.help_doc() with provider parameter."""

        def test_openai_shows_dev_commands(self) -> None:
            doc = ChatCommands.help_doc(provider=ProviderNames.OPENAI.value)
            assert "/dev" in doc
            assert "/developer" in doc
            assert "/dev-clear" in doc
            assert "/dev-show" in doc
            assert "/sys" not in doc

        def test_mistral_shows_sys_commands(self) -> None:
            doc = ChatCommands.help_doc(provider=ProviderNames.MISTRAL.value)
            assert "/sys" in doc
            assert "/system" in doc
            assert "/sys-clear" in doc
            assert "/sys-show" in doc
            assert "/dev" not in doc
            assert "/developer" not in doc

        def test_no_provider_shows_no_system_commands(self) -> None:
            doc = ChatCommands.help_doc()
            assert "/dev" not in doc
            assert "/sys" not in doc


class TestOpenaiUserRoles:
    """Tests for OpenaiUserRoles."""

    class TestSystemRole:
        """Tests for OpenaiUserRoles.system_role()."""

        def test_returns_developer(self) -> None:
            assert OpenaiUserRoles.system_role() == "developer"

        def test_returns_str(self) -> None:
            assert isinstance(OpenaiUserRoles.system_role(), str)


class TestMistralUserRoles:
    """Tests for MistralUserRoles."""

    class TestSystemRole:
        """Tests for MistralUserRoles.system_role()."""

        def test_returns_system(self) -> None:
            assert MistralUserRoles.system_role() == "system"

        def test_returns_str(self) -> None:
            assert isinstance(MistralUserRoles.system_role(), str)
