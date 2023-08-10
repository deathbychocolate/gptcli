"""
File to hold tests related to CLI
"""


from gptcli.src.chat import ChatOpenai


class TestCLI:
    def test_should_load_contents_of_text_file(self):
        ChatOpenai(
            context="on",
            filepath="t.txt",
            model="gpt-3.5-turbo",
            role_model="assistant",
            role_user="user",
            stream="on",
        )
        assert False
