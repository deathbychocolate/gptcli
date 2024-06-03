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
The project uses the openai API to query text from messages that we send via HTTP POST requests. This is respresented to the user as a MESSAGE-REPLY thread. You as the user send a message and the AI model replies. Meaning you will see something like this in your terminal:
```text
>>> [MESSAGE]: hi
>>> [REPLY, model=gpt-3.5-turbo]: Hello! How can I assist you today?
>>> [MESSAGE]: exit
```

# How do I get an API key?
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an openai account here: https://chat.openai.com/
- Generate an openai API key here: https://platform.openai.com/api-keys
