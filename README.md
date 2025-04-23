![PyPI](https://img.shields.io/pypi/v/dbc-gptcli?label=pypi%20version)
![Repo](https://img.shields.io/github/v/tag/deathbychocolate/gptcli?label=repo%20version)
![Supported Python Versions](https://img.shields.io/pypi/pyversions/dbc-gptcli)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dbc-gptcli)

# How do I run it?
- Pypi:
    - Open your preferred terminal.
    - Install the project via pypi using `pip install dbc-gptcli`.
    - Run `gptcli` or `gptcli [chat|se]`.
    - For more info on usage, check the builtin help docs using `gptcli -h` or `gptcli [chat|se] [-h|--help`.
- Docker:
    - Open your preferred terminal.
    - Start docker via the desktop app or running `sudo systemctl start docker`.
    - Pull the docker image with `docker pull deathbychocolate/gptcli:latest`.
    - Start and enter a container with `docker run --rm -it --entrypoint /bin/bash deathbychocolate/gptcli:latest`.
    - Run `gptcli` or `gptcli [chat|se]` or `python3 gptcli/main.py [chat|se]`.

# How do I get an API key?
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an OpenAI account here: https://chat.openai.com/
- Generate an OpenAI API key here: https://platform.openai.com/api-keys

# How do I setup the project for development?
These steps assume your system has the Python version indicated in the [Pipfile](./Pipfile) installed, are using VSCode, and have already run the program in `chat` mode at least once with a valid OpenAI API key. If you do not have the indicated Python version, it is recommended you install [homebrew](https://brew.sh/) and run `brew install python@3.11`.  

With that being said, you may complete the following steps:  
[1] Install [`miniconda`](https://www.anaconda.com/docs/getting-started/miniconda/install).  
[2] Open a terminal in your preferred directory; something like `~/Documents/Git/mine/`.  
[3] Run `git clone https://github.com/deathbychocolate/gptcli.git`.  
[4] Run `cd gptcli`.  
[5] Run `make setup`.  
[6] Run `make install`.  
[7] Run `pipenv shell`.  
[8] Run `gptcli [chat|se]` or `python3 gptcli/main.py [chat|se]`.  
[9] Run `make test` and `make coverage`.  
[10] Run [./gptcli/main.py](./gptcli/main.py) with VSCode's debug feature.

### Explanation:
[1] Miniconda sets up a default and always active virtual environment called `base`. This allows us to install packages without installing them system wide; thus avoiding use of `pip install --break-system-packages`.  

[5] Installs `python-dotenv`, `pipenv`, and `pre-commit` along with the rules in `.pre-commit-config`.  

[6] Installs project dependencies, type stubs, and the project in an editable state, allowing us to run `gptcli` as a terminal command and dynamically adding changes from the source code.  

[9] The first runs the tests using `pytest` and the second does the same but generates `coverage` html report as well in the project root. If both are generating only green output, it means the install process has been successful.  

[10] The project requires passing certain default values to trigger `chat` and `se`. This is because debug mode "skips" over argparse creating the default values we usually pass down the program's pipeline. To streamline things, the config needed has been added to [./vscode/launch.json](./.vscode/launch.json). To use it, you must set the current active file in VSCode to be [./gptcli/main.py](./gptcli/main.py) by opening the file in a tab and clicking in that file with your cursor. Then you may select VSCode's built-in *Run and Debug* feature (left hand side, under *Explorer*) and click the green arrow with the `Python Debugger: Current File with Arguments` option.  

# How do I use the project's Makefile?
From the project root directory, run `make` or `make help` to display all Makefile targets documentation.

# How does GPTCLI work?
The project uses the OpenAI API to query chat completions. It does so by sending message objects converted to JSON payloads and sent over HTTPS POST requests. For now, GPTCLI is for purely text based LLMs.

GPTCLI offers 2 modes to communicate with the LLM of your choosing, `Chat` and `Single-Exchange`:

`Chat` mode allows the user to have a conversation that is similar to ChatGPT by creating a MESSAGE-REPLY thread. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli chat
>>> hi
Hello! How can I assist you today?
>>> exit
username@hostname ~/>
```

`Chat` mode also allows for multiline correspondence. This is useful in cases where you would like to copy and paste small to medium-large text or code samples; though there is no size limit. You may enter and exit this feature by typing and entering `"""` in the prompt. For example, you should see output similar to the following:
```text
username@hostname ~/> gptcli chat
>>> """
... What is the expected output of this code? Be concise.
...
... import json
... payload: dict = {'a': 1, 'b': 2}
... print(json.dumps(payload, indent=4))
... """
The output is a pretty-printed JSON string of the dictionary:

{
    "a": 1,
    "b": 2
}

>>> exit
username@hostname ~/>
```

`Single-Exchange` is functionally similar to `Chat`, but it only allows a single exchange of messages to happen (1 sent from client-side, 1 response message from server-side) and then exit. This encourages loading all the context and instructions in one message. It is also more suitable for automating multiple calls to the API with different payloads, and flags. This mode will show you output similar to the following:
```text
username@hostname ~/> gptcli se "hello"
Hello! How can I assist you today?
username@hostname ~/>
```

# How is GPTCLI different from other clients?
- GPTCLI does not use any software developed by OpenAI. For example, it does not use the `openai` package supported by OpenAI (found [here](https://github.com/openai/openai-python?tab=readme-ov-file)), there are simply too many features in it that go unused (>200 MB) when for now we only really need 50-100 lines of Python code.
- GPTCLI prioritizes features that make CLI usage easy and useful.
- GPTCLI aims to eventually have all the features of ChatGPT in the terminal.
