# What is it?
This is a simple python project that aims to provide a command line interface for communicating with OpenAIs AI models and provide voice based reponses.

# How does it work?
The project uses the official OpenAI SDK named openai. This SDK is a very comprenhensive CLI based python project of which we use only the Completions features. I recommend you investigate this further  by installing it using the following command:

```
python3 -m pip3 install openai
```

The project also uses the official AWS SDK named boto3. This SDK is a very comprenhensive python module which we use to communicate with AWS's Polly service; a text to speech service (TTS). I recommend experimenting with it once installed with the following command:
```
python3 -m pip3 install boto3
```


# Before running the project:
- Create an openai account [here](https://chat.openai.com/).
- Generate an openai API key [here](https://platform.openai.com/account/api-keys).
- Export the API key in your current bash session using the following command:
```
export OPENAI_API_KEY=<API-KEY>
```
- Install AWS CLI by following the official guide found [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
- Create an AWS account [here](https://aws.amazon.com/).
- Follow the AWS SSO setup found [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).
- Authenticate yourself to AWS using the following command:
```
aws sso login --profile <YOUR_PROFILE_NAME>
```
- Export the SSO name to your local environment with the following command:
```
export AWS_SSO_PROFILE_NAME=<YOUR_AWS_SSO_PROFILE_NAME>
```

# How do I run it?
You may run the project by entering main.py at the root of the project, updating the string currently there with your text, save, and run.
