# GPTCLI
### How do I run it?
Run ```python3 main.py``` in the project root directory.

### Are there any project requirements?
Yes, to install them simply run the following command in the project root directory:
```
python3 -m pip install -r requirements.txt
```
Also, you need a valid openai API key. See below to generate one.

### What is it?
A CLI version of chatGPT, plus features.

### How does it work?
The project uses the official OpenAI SDK named openai. This SDK is a very comprenhensive CLI based python project of which we use only the Completions features. I recommend you investigate this further using the official openai docs.

### Before running the project:
You need valid OpenAI credentials to communicate with the AI models. To do this, follow the points below:
- Create an openai account here: https://chat.openai.com/
- Generate an openai API key here: https://platform.openai.com/account/api-keys
