"""File that will hold all the tests relating to message.py."""

from typing import Any, Generator

import pytest
from tiktoken import Encoding

from gptcli.src.common.constants import (
    OpenaiModelsChat,
    OpenaiUserRoles,
    ProviderNames,
)
from gptcli.src.common.message import Message, MessageFactory, Messages


class TestMessage:
    """Holds tests for the Message class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Message, None, None]:
        """Generate a message object."""
        message: Message = Message(
            role="user",
            content="Test.",
            model="gpt-4-turbo",
            provider=ProviderNames.OPENAI.value,
            is_reply=False,
        )
        yield message

    class TestNumberOfTokensFromMessage:
        """Holds tests for _count_tokens()."""

        def test_should_raise_error_for_not_implemented_model(self) -> None:
            with pytest.raises(NotImplementedError):
                Message(
                    role="user",
                    content="Test.",
                    model="gpt-xxx",
                    provider=ProviderNames.OPENAI.value,
                    is_reply=False,
                )

        def test_should_return_an_integer(self, setup_teardown: Message) -> None:
            message: Message = setup_teardown
            tokens: int = message._count_tokens(provider=ProviderNames.OPENAI.value)
            assert isinstance(tokens, int)

    class TestEncoding:
        """Holds tests for _encoding_openai()."""

        def test_should_return_o200k_base_for_supported_model_gpt_4o(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-4o",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = message._encoding_openai()
            assert encoding.name == "o200k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_4_turbo(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = message._encoding_openai()
            assert encoding.name == "cl100k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_4(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-4",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = message._encoding_openai()
            assert encoding.name == "cl100k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_3_5_turbo(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-3.5-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = message._encoding_openai()
            assert encoding.name == "cl100k_base"

        def test_should_return_an__encoding(self, setup_teardown: Message) -> None:
            message = setup_teardown
            encoding: Encoding = message._encoding_openai()
            assert isinstance(encoding, Encoding)

    class TestToDictionaryReducedContext:
        """Holds tests for to_dict_reduced_context()."""

        @pytest.mark.parametrize("variable", ["role", "content"])
        def test_should_contain_these_variables(self, variable: str, setup_teardown: Message) -> None:
            message = setup_teardown
            keys = message.to_dict_reduced_context().keys()
            assert variable in keys

        def test_should_return_a_dictionary(self, setup_teardown: Message) -> None:
            message = setup_teardown
            context = message.to_dict_reduced_context()
            assert isinstance(context, dict)

    class TestToDictionaryFullContext:
        """Holds tests for to_dict_full_context()."""

        @pytest.mark.parametrize("variable", ["role", "content", "model", "is_reply", "tokens"])
        def test_should_contain_these_variables(self, variable: str, setup_teardown: Message) -> None:
            context = setup_teardown
            keys = context.to_dict_full_context().keys()
            assert variable in keys

        def test_should_return_a_dictionary(self, setup_teardown: Message) -> None:
            message = setup_teardown
            context = message.to_dict_full_context()
            assert isinstance(context, dict)


class TestMessageFactory:
    """Holds tests for the MessageFactory class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[MessageFactory, None, None]:
        """Generate a MessageFactory object."""
        message_factory: MessageFactory = MessageFactory(provider=ProviderNames.OPENAI.value)
        yield message_factory

    class TestCreateUserMessage:
        """Holds tests for create_user_message()."""

        def test_should_create_a_message_where_the_reply_bool_is_false(self, setup_teardown: MessageFactory) -> None:
            message_factory: MessageFactory = setup_teardown
            message = message_factory.user_message(role="user", content="Test.", model="gpt-4-turbo")
            assert message._is_reply is False

        def test_should_return_a_message(self, setup_teardown: MessageFactory) -> None:
            message_factory: MessageFactory = setup_teardown
            message = message_factory.user_message(role="user", content="Test.", model="gpt-4-turbo")
            assert isinstance(message, Message)

    class TestCreateReplyMessage:
        """Holds tests for create_reply_message()."""

        def test_should_create_a_message_where_the_reply_bool_is_true(self, setup_teardown: MessageFactory) -> None:
            message_factory: MessageFactory = setup_teardown
            message = message_factory.reply_message(content="Test.", model="gpt-4-turbo")
            assert message._is_reply is True

        def test_should_return_a_message(self, setup_teardown: MessageFactory) -> None:
            message_factory: MessageFactory = setup_teardown
            message = message_factory.reply_message(content="Test.", model="gpt-4-turbo")
            assert isinstance(message, Message)

    class TestCreateMessageFromDict:
        """Holds tests for create_message_from_dict()."""

        def test_should_return_a_type_error_when_passing_a_non_dict_parameter(
            self, setup_teardown: MessageFactory
        ) -> None:
            with pytest.raises(TypeError):
                message_factory: MessageFactory = setup_teardown
                message: list[str] = ["", ""]
                message_factory.message_from_dict(message=message)  # type: ignore[arg-type]

        def test_should_return_a_message(self, setup_teardown: MessageFactory) -> None:
            message_factory: MessageFactory = setup_teardown
            message: dict[str, Any] = {
                "created": 1717265555.4425488,
                "uuid": "238555b5-98f8-4ead-8cb7-8d14283aa3fe",
                "role": OpenaiUserRoles.default(),
                "content": "assistant",
                "model": OpenaiModelsChat.GPT_4_TURBO.value,
                "provider": ProviderNames.OPENAI.value,
                "is_reply": True,
                "tokens": 0,
                "index": 0,
            }
            m: Message = message_factory.message_from_dict(message=message)
            assert isinstance(m, Message)


class TestMessages:
    """Holds tests for the Messages class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self) -> Generator[Messages, None, None]:
        """Generate a Message object."""
        message = Message(
            role=OpenaiUserRoles.default(),
            content="Test.",
            model=OpenaiModelsChat.GPT_4_TURBO.value,
            provider=ProviderNames.OPENAI.value,
            is_reply=False,
        )
        messages: Messages = Messages(messages=[message])
        yield messages

    class TestAddMessage:
        """Holds tests for add_message()."""

        def test_should_not_add_message_when_message_is_none(self, setup_teardown: Messages) -> None:
            messages: Messages = setup_teardown
            messages_count_before: int = len(messages)
            messages.add(message=None)
            messages_count_after: int = len(messages)
            assert messages_count_before == messages_count_after

        def test_should_add_message_when_we_add_valid_message_object(self, setup_teardown: Messages) -> None:
            messages: Messages = setup_teardown
            messages_count_before: int = len(messages)
            message: Message = Message(
                role=OpenaiUserRoles.default(),
                content="Test.",
                model=OpenaiModelsChat.GPT_4_TURBO.value,
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages.add(message=message)
            messages_count_after: int = len(messages)
            assert messages_count_before + 1 == messages_count_after

        def test_should_increase_token_count_when_we_add_valid_message_object(self, setup_teardown: Messages) -> None:
            messages: Messages = setup_teardown
            messages_token_count_before: int = messages.tokens
            message: Message = Message(
                role=OpenaiUserRoles.default(),
                content="Test.",
                model=OpenaiModelsChat.GPT_4_TURBO.value,
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages.add(message=message)
            messages_token_count_after: int = messages.tokens
            assert messages_token_count_before < messages_token_count_after

    class TestCountTokens:
        """Holds tests for _count_tokens()."""

        def test_should_return_an_integer(self, setup_teardown: Messages) -> None:
            messages: Messages = setup_teardown
            count: int = messages._count_tokens()
            assert isinstance(count, int)

        def test_should_return_a_positive_value(self, setup_teardown: Messages) -> None:
            messages: Messages = setup_teardown
            count: int = messages._count_tokens()
            assert count >= 0
