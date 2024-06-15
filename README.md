# How do I run it?
- Users:
    - A user should only have to run `gptcli` in their preferred terminal.
    - For more info on usage, check the builtin help docs using `gptcli [-h|--help]`
- Developers:
    - Open your preferred terminal.
    - Clone the project to your local machine using: `git clone <https_link|ssh_link>`
    - Change your current working directory to the project root.
    - Install pipenv using: `python3 -m pip install pipenv`
    - Enter a pipenv shell using: `pipenv shell`
    - Install dependencies using: `pipenv install`
    - Make the project editable: `pip install --editable .`
    - Run `gptcli`

# How do I run the tests?
- Developers:
    - Follow the `How do I run it?` above.
    - Run the following command in the root of the project: `pytest --cov=gptcli/src/ --cov-report html --log-cli-level=ERROR`. This will generate a coverage report named htmlcov at the root of the project.

# How does it work?
The project uses the OpenAI API to query text using client sent messages sent over HTTP POST requests. There are 2 modes to consider, `Chat` and `Single-Exchange`:

`Chat` mode allows the user to have a conversation that is similar to ChatGPT by creating a MESSAGE-REPLY thread. This mode will show you output similar to the following:
```text
>>> [MESSAGE]: hi
>>> [REPLY, model=gpt-3.5-turbo]: Hello! How can I assist you today?
>>> [MESSAGE]: exit
```

`Single-Exchange` is funcationally similar to `Chat`, but it only allows a single exchange of messages to happen (1 sent from client-side, 1 from server-side) and then exit. This encourages loading all the context and instructions in one message. It is also more suitable for automation. This mode will show you ouput similar to the following:
```text
username@hostname ~/> gptcli se "hello"
Hello! How can I assist you today?
username@hostname ~/>
```

# How do I get an API key?
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an openai account here: https://chat.openai.com/
- Generate an openai API key here: https://platform.openai.com/api-keys
