![PyPI](https://img.shields.io/pypi/v/dbc-gptcli?label=pypi%20package)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dbc-gptcli)

# How do I run it?
- Users:
    - A user should only have to run `gptcli chat` or `gptcli se` in their preferred terminal.
    - For more info on usage, check the builtin help docs using `gptcli [chat|se] [-h|--help]`
- Developers:
    - Cloning the repo:
        - Open your preferred terminal.
        - Clone the project to your local machine using: `git clone <https_link|ssh_link>`
        - Change your current working directory to the project root.
        - Execute the following command: `make install`
        - Run `gptcli`
    - Running the Docker image via a Docker container:
        - Open your preferred terminal.
        - Enter switch to the root user.
        - Start docker: `systemctl start docker`
        - Pull the docker image: `docker pull deathbychocolate/gptcli:latest`
        - Enter the image: `docker exec -it <container_name> bash`

# How do I run the tests?
- Follow the `How do I run it?` above and then choose:
    - Run the tests: `make test`
    - Run the tests and generate a coverage report: `make coverage`

# How does it work?
The project uses the OpenAI API to query text using client sent messages sent over HTTP POST requests. There are 2 modes to consider, `Chat` and `Single-Exchange`:

`Chat` mode allows the user to have a conversation that is similar to ChatGPT by creating a MESSAGE-REPLY thread. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli chat
>>> [MESSAGE]: hi
>>> [REPLY, model=gpt-3.5-turbo]: Hello! How can I assist you today?
>>> [MESSAGE]: exit
username@hostname ~/>
```

`Single-Exchange` is functionally similar to `Chat`, but it only allows a single exchange of messages to happen (1 sent from client-side, 1 from server-side) and then exit. This encourages loading all the context and instructions in one message. It is also more suitable for automation. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli se "hello"
Hello! How can I assist you today?
username@hostname ~/>
```

# How do I get an API key?
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an openai account here: https://chat.openai.com/
- Generate an openai API key here: https://platform.openai.com/api-keys
