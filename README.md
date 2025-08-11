![PyPI](https://img.shields.io/pypi/v/dbc-gptcli?label=PyPI%20version)
![Repo](https://img.shields.io/github/v/tag/deathbychocolate/gptcli?label=Repo%20version)
![Supported Python Versions](https://img.shields.io/pypi/pyversions/dbc-gptcli)
![Supported OS](https://img.shields.io/badge/Supported%20OS-Linux%20%7C%20MacOS%20-blueviolet)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/dbc-gptcli?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=downloads)](https://pepy.tech/projects/dbc-gptcli)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/dbc-gptcli?period=month&units=international_system&left_color=grey&right_color=brightgreen&left_text=downloads/month)](https://pepy.tech/projects/dbc-gptcli)

# How do I run it?
- Pypi:
    - Open your preferred terminal.
    - Install the project via pypi using `pip install dbc-gptcli`.
    - Run `gptcli [mistral|openai] [chat|se]`.
    - For more info on usage, check the builtin help docs using:
      - `gptcli -h`
      - `gptcli [mistral|openai] [-h|--help]`
      - `gptcli [mistral|openai] [chat|se] [-h|--help]`.
- Docker:
    - Open your preferred terminal.
    - Start docker via the desktop app or running `sudo systemctl start docker`.
    - Pull the docker image with `docker pull deathbychocolate/gptcli:latest`.
    - Start and enter a container with `docker run --rm -it --entrypoint /bin/bash deathbychocolate/gptcli:latest`.
    - Run `gptcli [mistral|openai] [chat|se]` or `python3 gptcli/main.py [mistral|openai] [chat|se]`.

# How do I get an API key?
You need valid API keys to communicate with the AI models.

For OpenAI:
- Create an OpenAI account here: https://chat.openai.com/
- Generate an OpenAI API key here: https://platform.openai.com/api-keys

For Mistral AI:
- Create a Mistral AI account here: https://chat.mistral.ai/chat
- Generate a Mistral AI API key here: https://console.mistral.ai/api-keys

# How does GPTCLI work?
The project uses the OpenAI API to query chat completions. It does so by sending message objects converted to JSON payloads and sent over HTTPS POST requests. For now, GPTCLI is for purely text based LLMs.

GPTCLI facilitates access to 2 LLM providers, Mistral AI and OpenAI. Each provider offers 2 modes to communicate with the LLM of your choosing, `Chat` and `Single-Exchange`:

`Chat` mode allows the user to have a conversation that is similar to ChatGPT by creating a MESSAGE-REPLY thread. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli openai chat
>>> hi
>>> Hello! How can I assist you today?
>>> /q
username@hostname ~/>
```

`Chat` mode also allows for multiline correspondence. This is useful in cases where you would like to copy and paste small to medium-large text or code samples; though there is no size limit. You may enter and exit this feature by typing and entering `/m` in the prompt. For example, you should see output similar to the following:
```text
username@hostname ~/> gptcli openai chat
>>> /m
... What is the expected output of this code? Be concise.
...
... import json
... payload: dict = {'a': 1, 'b': 2}
... print(json.dumps(payload, indent=4))  # Hit [ESC] followed by [ENTER] here
>>> The output is a pretty-printed JSON string of the dictionary:

{
    "a": 1,
    "b": 2
}

>>> /q
username@hostname ~/>
```

`Chat` mode also allows loading of the last chat session as your current session. For example:
```text
username@hostname ~/> gptcli openai chat --load-last
>>> What is the expected output of this code? Be concise.

import json
payload: dict = {'a': 1, 'b': 2}
print(json.dumps(payload, indent=4))  # Hit [ESC] followed by [ENTER] here
>>> The output is a pretty-printed JSON string of the dictionary:

{
    "a": 1,
    "b": 2
}

>>> Send a message (/? for help)
```

`Chat` mode also allows for in-chat commands. For example:
```text
username@hostname ~/> gptcli openai chat
>>> /?

/?, /h, /help           Show help.
/c, /cls, /clear        Clear screen.
/m, /mult               Enter multiline mode.
/e, /exit, /q, /quit    End program.
↑/↓                     Navigate history.
Enter                   Send message.

>>> Send a message (/? for help)
```

`Single-Exchange` is functionally similar to `Chat`, but it only allows a single exchange of messages to happen (1 sent from client-side, 1 response message from server-side) and then exit. This encourages loading all the context and instructions in one message. It is also more suitable for automating multiple calls to the API with different payloads, and flags. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli openai se "hello"
Hello! How can I assist you today?
username@hostname ~/>
```

# How is GPTCLI different from other clients?
- GPTCLI does not use any software developed by OpenAI or Mistral AI, except for tokenization (ie tiktoken, and mistral-common).
- GPTCLI prioritizes features that make the CLI useful and easy to use.
- GPTCLI aims to eventually have all the features of its WebApp counterparts in the terminal.
