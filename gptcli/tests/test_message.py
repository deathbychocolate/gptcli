"""File that will hold all the tests relating to Message.py."""

import pytest

from gptcli.src.message import Message, MessageFactory, Messages


class TestMessage: 
    """Holds tests for the Message class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self):
        message = Message(role="user", content="A very basic message.", model="gpt-4", is_reply=False)
        yield message

    class TestNumberOfTokensFromMessage:

        def test_should_raise_error_for_not_implemented_model(self) -> None:
            with pytest.raises(NotImplementedError):
                Message(role="user", content="A very basic message.", model="gpt-xxx", is_reply=False)

        def test_should_return_an_integer(self, setup_teardown: Message) -> None:
            message = setup_teardown
            tokens = message.number_of_tokens_from_message()
            assert isinstance(tokens, int)


    class TestToDictionaryReducedContext:
        """Holds tests for to_dictionary_reduced_context()."""

        @pytest.mark.parametrize("variable", ["role", "content"])
        def test_should_contain_these_variables(self, variable: str, setup_teardown: Message) -> None:
            message = setup_teardown
            keys = message.to_dictionary_reduced_context().keys()
            assert variable in keys

        def test_should_return_a_dictionary(self, setup_teardown) -> None:
            message = setup_teardown
            context = message.to_dictionary_reduced_context()
            assert isinstance(context, dict)

    class TestToDictionaryFullContext:
        """Holds tests for to_dictionary_full_context()."""

        @pytest.mark.parametrize("variable", ["role", "content", "model", "is_reply", "tokens"])
        def test_should_contain_these_variables(self, variable: str, setup_teardown: Message) -> None:
            context = setup_teardown
            keys = context.to_dictionary_full_context().keys()
            assert variable in keys

        def test_should_return_a_dictionary(self, setup_teardown: Message) -> None:
            message = setup_teardown
            context = message.to_dictionary_full_context()
            assert isinstance(context, dict)


class TestMessageFactory:
    """Holds tests for the MessageFactory class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self):
        message_factory = MessageFactory()
        yield message_factory

    class TestCreateUserMessage:
        """Holds tests for create_user_message()."""

        def test_should_create_a_message_where_the_reply_bool_is_false(self, setup_teardown: MessageFactory) -> None:
            message_factory = setup_teardown
            message = message_factory.create_user_message(role="user", content="A very basic message.", model="gpt-4")
            assert message._is_reply is False  # pylint: disable=W0212:protected-access

        def test_should_return_a_message(self, setup_teardown) -> None:
            message_factory = setup_teardown
            message = message_factory.create_user_message(role="user", content="A very basic message.", model="gpt-4")
            assert isinstance(message, Message)

    class TestCreateReplyMessage:
        """Holds tests for create_reply_message()."""

        def test_should_create_a_message_where_the_reply_bool_is_true(self, setup_teardown: MessageFactory) -> None:
            message_factory = setup_teardown
            message = message_factory.create_reply_message(role="user", content="A very basic message.", model="gpt-4")
            assert message._is_reply is True  # pylint: disable=W0212:protected-access

        def test_should_return_a_message(self, setup_teardown) -> None:
            message_factory = setup_teardown
            message = message_factory.create_reply_message(role="user", content="A very basic message.", model="gpt-4")
            assert isinstance(message, Message)


class TestMessages:
    """Holds tests for the Messages class."""

    @pytest.fixture(scope="session")
    def setup_teardown(self):
        message = Message(role="user", content="A very basic message.", model="gpt-4", is_reply=False)
        messages: Messages = Messages(messages=[message])
        yield messages

    class TestAddMessage():
        """Holds tests for add_message()."""

        def test_should_not_add_message_when_message_is_none(self, setup_teardown):
            messages: Messages = setup_teardown
            messages_count_before: int = len(messages)
            message: Message = None
            messages.add_message(message=message)
            messages_count_after: int = len(messages)
            assert messages_count_before == messages_count_after

        def test_should_add_message_when_we_add_valid_message_object(self, setup_teardown):
            messages: Messages = setup_teardown
            messages_count_before: int = len(messages)
            message: Message = Message(role="user", content="A very basic message.", model="gpt-4", is_reply=False)
            messages.add_message(message=message)
            messages_count_after: int = len(messages)
            assert messages_count_before + 1 == messages_count_after

        def test_should_increase_token_count_when_we_add_valid_message_object(self, setup_teardown):
            messages: Messages = setup_teardown
            messages_token_count_before: int = messages.tokens
            message: Message = Message(role="user", content="A very basic message.", model="gpt-4", is_reply=False)
            messages.add_message(message=message)
            messages_token_count_after: int = messages.tokens
            assert messages_token_count_before < messages_token_count_after

    class TestCountTokens():
        """Holds tests for _count_tokens()."""

        def test_should_return_an_integer(self, setup_teardown):
            messages: Messages = setup_teardown
            count: int = messages._count_tokens()  # pylint: disable=W0212:protected-access
            assert isinstance(count, int)

        def test_should_return_a_positive_value(self, setup_teardown):
            messages: Messages = setup_teardown
            count: int = messages._count_tokens()  # pylint: disable=W0212:protected-access
            assert count >= 0
