"""File that will hold all the tests relating to message.py."""

from typing import Any, Generator

import pytest
from tiktoken import Encoding

from gptcli.src.common.constants import (
    MistralModelsChat,
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
            encoding: Encoding = Message._encoding_openai(message._model)
            assert encoding.name == "o200k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_4_turbo(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = Message._encoding_openai(message._model)
            assert encoding.name == "cl100k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_4(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-4",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = Message._encoding_openai(message._model)
            assert encoding.name == "cl100k_base"

        def test_should_return_cl100k_base_for_supported_model_gpt_3_5_turbo(self) -> None:
            message: Message = Message(
                role="user",
                content="Test.",
                model="gpt-3.5-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            encoding: Encoding = Message._encoding_openai(message._model)
            assert encoding.name == "cl100k_base"

        def test_should_return_an__encoding(self, setup_teardown: Message) -> None:
            message = setup_teardown
            encoding: Encoding = Message._encoding_openai(message._model)
            assert isinstance(encoding, Encoding)

    class TestRoleProperty:
        """Holds tests for the role property."""

        def test_should_return_role_value(self, setup_teardown: Message) -> None:
            assert setup_teardown.role == "user"

        def test_should_return_str(self, setup_teardown: Message) -> None:
            assert isinstance(setup_teardown.role, str)

        def test_should_return_developer_role(self) -> None:
            message = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            assert message.role == "developer"

        def test_should_return_system_role(self) -> None:
            message = Message(
                role="system",
                content="You are a pirate.",
                model=MistralModelsChat.default(),
                provider=ProviderNames.MISTRAL.value,
                is_reply=False,
            )
            assert message.role == "system"

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

    class TestFlushExcept:
        """Holds tests for flush_except()."""

        def test_keeps_only_matching_roles(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev_msg = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            assistant_msg = Message(
                role="assistant",
                content="Ahoy!",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=True,
            )
            messages = Messages(messages=[user_msg, dev_msg, assistant_msg])
            messages.flush_except({"developer"})
            assert len(messages) == 1
            remaining = next(iter(messages))
            assert remaining.role == "developer"

        def test_updates_token_count(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev_msg = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[user_msg, dev_msg])
            messages.flush_except({"developer"})
            assert messages.tokens == dev_msg.tokens

        def test_flushes_all_when_no_roles_match(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[user_msg])
            messages.flush_except({"developer"})
            assert len(messages) == 0
            assert messages.tokens == 0

    class TestRemoveByRoleAndIndex:
        """Holds tests for remove_by_role_and_index()."""

        def test_removes_correct_message(self) -> None:
            dev1 = Message(
                role="developer",
                content="First.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev2 = Message(
                role="developer",
                content="Second.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[dev1, user_msg, dev2])
            result = messages.remove_by_role_and_index("developer", 1)
            assert result is True
            assert len(messages) == 2
            roles = [m.role for m in messages]
            assert roles == ["developer", "user"]

        def test_returns_false_for_out_of_range_index(self) -> None:
            dev_msg = Message(
                role="developer",
                content="Only one.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[dev_msg])
            result = messages.remove_by_role_and_index("developer", 5)
            assert result is False
            assert len(messages) == 1

        def test_returns_false_for_negative_index(self) -> None:
            dev_msg = Message(
                role="developer",
                content="Only one.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[dev_msg])
            result = messages.remove_by_role_and_index("developer", -1)
            assert result is False

        def test_updates_token_count(self) -> None:
            dev_msg = Message(
                role="developer",
                content="Remove me.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[dev_msg, user_msg])
            tokens_before = messages.tokens
            dev_tokens = dev_msg.tokens
            messages.remove_by_role_and_index("developer", 0)
            assert messages.tokens == tokens_before - dev_tokens

    class TestFlushByRole:
        """Holds tests for flush_by_role()."""

        def test_removes_matching_messages(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev_msg = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            assistant_msg = Message(
                role="assistant",
                content="Ahoy!",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=True,
            )
            messages = Messages(messages=[user_msg, dev_msg, assistant_msg])
            messages.flush_by_role({"developer"})
            assert len(messages) == 2

        def test_leaves_non_matching_messages(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev_msg = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[user_msg, dev_msg])
            messages.flush_by_role({"developer"})
            remaining_roles = [m.role for m in messages]
            assert remaining_roles == ["user"]

        def test_updates_token_count(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            dev_msg = Message(
                role="developer",
                content="You are a pirate.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[user_msg, dev_msg])
            tokens_before = messages.tokens
            dev_tokens = dev_msg.tokens
            messages.flush_by_role({"developer"})
            assert messages.tokens == tokens_before - dev_tokens

        def test_no_op_when_no_matching_roles(self) -> None:
            user_msg = Message(
                role="user",
                content="Hello.",
                model="gpt-4-turbo",
                provider=ProviderNames.OPENAI.value,
                is_reply=False,
            )
            messages = Messages(messages=[user_msg])
            messages.flush_by_role({"developer"})
            assert len(messages) == 1

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


class TestMistralSystemTokenizer:
    """Tests for Mistral tokenizer handling of system role messages."""

    def test_system_role_message_tokenizes_successfully(self) -> None:
        message = Message(
            role="system",
            content="You are a helpful assistant.",
            model=MistralModelsChat.default(),
            provider=ProviderNames.MISTRAL.value,
            is_reply=False,
        )
        assert message.tokens > 0

    def test_system_role_returns_integer_token_count(self) -> None:
        message = Message(
            role="system",
            content="You are a pirate.",
            model=MistralModelsChat.default(),
            provider=ProviderNames.MISTRAL.value,
            is_reply=False,
        )
        assert isinstance(message.tokens, int)
