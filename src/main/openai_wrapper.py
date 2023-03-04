"""
Contains a wrapper for the openai SDK
"""
import openai


class Message:
    """
    A message that will be fed to openai

    Attributes:
        role: The role of the message
        content: The content of the message
    """

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def dictionary(self):
        """
        Returns a dictionary representation of the message

        :return: a dictionary
        """
        return {"role": self.role, "content": self.content}


class MessageFactory:
    """
    A factory for creating messages
    """

    @staticmethod
    def create_message(role: str, content: str):
        """
        Creates a message

        :param role: The role of the message
        :param content: The content of the message
        :return: A message
        """
        return Message(role, content).dictionary()


class OpenAIWrapper:
    """
    A wrapper for the openai python library
    """

    ENGINE = "gpt-3.5-turbo"
    MAX_TOKENS = 4096  # The limit as defined by openai docs

    def __init__(self, questions: str):
        """
        XXX
        """
        pass

    def ask(self, model: str, messages: list):
        """
        Asks openai a question

        :param model: The model to use
        :param messages: The messages to use
        :return: The response from openai
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )

        return response["choices"][0]["message"]["content"]


def main():
    """
    Start here
    """
    response = OpenAIWrapper("").ask(
        model=OpenAIWrapper.ENGINE,
        messages=[MessageFactory.create_message("user", "Hello!")],
    )
    print(response)


if __name__ == "__main__":
    main()
