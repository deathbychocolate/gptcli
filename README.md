# Polly
A class that uses the boto3 SDK to create an aws polly client, along with some needed methods to feed text generate audio with ease.

# Openai
A class that uses the openai module needed to communicate with the openai API. It's purpose is to generate the text to be fed to polly.


# Before running the project:
- Creata an openai account [here](https://chat.openai.com/).
- Generate an openai API key [here](https://platform.openai.com/account/api-keys).
- Export the API key in your current bash session using the following command:
```
export OPENAI_API_KEY=<API-KEY>
```
- Install AWS CLI by following the official guide found [here](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
- Follow the AWS SSO setup found [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html).
- Authenticate yourself to AWS using the foloowing command:
```
aws sso login
```