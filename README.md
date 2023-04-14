# How do I run it?
- Users:
    - A user should only have to run ```gptcli``` in their machine's terminal.

- Developers:
    - Install pipenv using: ```python3 -m pip pipenv```
    - Enter a pipenv shell using: ```pipenv shell```
    - Install dependencies using: ```pipenv install```
    - Run ```python3 main.py``` in the project root directory.

# How does it work?
It uses the openai API to query text from messages that we send via HTTP POST requests.This is respresented to the user as a USER-AI relationship. Meaning you will see something like this in your terminal:
```text
>>> [USER]: hi
>>> [AI, model=gpt-3.5-turbo]: Hello! How can I assist you today?
>>> [USER]: exit
```

# Before running the project:
You need valid OpenAI credentials to communicate with the AI models. To do this:
- Create an openai account here: https://chat.openai.com/
- Generate an openai API key here: https://platform.openai.com/account/api-keys
