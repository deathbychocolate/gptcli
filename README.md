# What is it?
A CLI version of chatGPT, plus features.

# How does it work?
The project uses the official OpenAI SDK named openai. This SDK is a very comprenhensive CLI based python project of which we use only the Completions features. I recommend you investigate this further using the official openai docs.

# How do I get started?
Simply install the requirements by runnning:
```
python3 -m pip install -r requirements.txt
```

# Before running the project:
- Create an openai account [here](https://chat.openai.com/).
- Generate an openai API key [here](https://platform.openai.com/account/api-keys).
- Export the API key in your current bash session using the following command:
```
export OPENAI_API_KEY=<API-KEY>
```

# How do I run it?
Run ```python3 main.py``` in the project root directory.
