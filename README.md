![PyPI](https://img.shields.io/pypi/v/dbc-gptcli?label=pypi%20package)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dbc-gptcli)

# How do I run it?
- Users:
    - Open your preferred terminal.
    - Install the project via pypi using `pip install dbc-gptcli` or `python3 -m pip install dbc-gptcli`
    - A user should only have to run `gptcli chat` or `gptcli se`.
    - For more info on usage, check the builtin help docs using `gptcli [chat|se] [-h|--help]`
- Developers:
    - Cloning the repo:
        - Open your preferred terminal.
        - Clone the project to your local machine using: `git clone [<https_link>|<ssh_link>]`
        - Change your current working directory to the project root.
        - Execute the following command: `make install`
        - Run `gptcli [chat|se]`. If installed python packages are not in your system's PATH (as is the case for MacOS), run `python3 gptcli/main.py [chat|se]`
    - Running the Docker image via a Docker container:
        - Open your preferred terminal.
        - Enter switch to the root user.
        - Start docker: `systemctl start docker`
        - Pull the docker image: `docker pull deathbychocolate/gptcli:latest`
        - Enter the image: `docker exec -it <container_name> bash`

# How do I get an API key?
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an OpenAI account here: https://chat.openai.com/
- Generate an OpenAI API key here: https://platform.openai.com/api-keys

# How do I use the project's Makefile?
From the project root directory, run `make` or `make help` to display all Makefile targets documentation.

# How does GPTCLI work?
The project uses the OpenAI API to query chat completions. It does so by sending message objects converted to JSON payloads and sent over HTTPS POST requests. For now, GPTCLI is for purely text based LLMs.

GPTCLI offers 2 modes to communicate with the LLM of your choosing, `Chat` and `Single-Exchange`:

`Chat` mode allows the user to have a conversation that is similar to ChatGPT by creating a MESSAGE-REPLY thread. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli chat
>>> [MESSAGE]: hi
>>> [REPLY, model=gpt-3.5-turbo]: Hello! How can I assist you today?
>>> [MESSAGE]: exit
username@hostname ~/>
```

`Single-Exchange` is functionally similar to `Chat`, but it only allows a single exchange of messages to happen (1 sent from client-side, 1 response message from server-side) and then exit. This encourages loading all the context and instructions in one message. It is also more suitable for automating multiple calls to the API with different payloads, and flags. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli se "hello"
Hello! How can I assist you today?
username@hostname ~/>
```

# How is GPTCLI different from other clients?
- The philosophy behind GPTCLI is to offer the features of ChatGPT in the terminal. This means that the user should eventually have all the features that ChatGPT offers in the webapp. However, we are not creating a 'ChatGPT webapp, but in the terminal'. Other useful features that are not available in ChatGPT could be added.

- GPTCLI does not use any software developed by OpenAI. For example, it does not use the `openai` package supported by OpenAI (found [here](https://github.com/openai/openai-python?tab=readme-ov-file)), there are simply too many features in it that go unused (>200 MB) when for now we only really need 50-100 lines of Python code.

- GPTCLI prioritizes making features that make CLI based usage easy and useful.
