## 0.18.0 (2024-12-23)

### Feat

- **project**: Add minimum necessary changes to mypycify the project and remove sseclient module from project.

### Fix

- Fix spelling.
- Fix bug with finding correct encoding for messages.
- Fix typing issue found by mypy.
- Fix broken make clean command.

### Refactor

- **project**: Major changes going in.
- Add type hint and fix spelling.
- Add type hint for logger.
- Make it more obvious the default value needs to be overwritten.
- **chat**: Improve chat readability, coverage, reply process, and abort process.
- Since we always expect response to be a Response object, it could never be None.

## 0.17.0 (2024-07-19)

### Feat

- **project**: Add 'gpt-4o mini' as an option to model selection.

### Refactor

- **project**: :see_no_evil: Remove outdated custom list and include vscode config files.
- **project**: Remove unused comments and change the workdir name as to not be confusing when are project's root dir is '/gptcli/gptcli/. '.
- **makefile**: Hide the command executed from stdout using @.
- **project**: Remove uneeded version variables.
- **project**: Remove code for speech feature.

## 0.16.2 (2024-07-06)

### Fix

- **project**: Fix missing module error with pypdf and move all configurations to toml from setup.py.
- **message**: Incorporate the new encodings for Openai's LLMs.

## 0.16.1 (2024-07-05)

### Fix

- **docker**: Fix issue with docker image not building.

## 0.16.0 (2024-06-29)

### Feat

- :sparkles: Add option to select extraction type.
- **project**: Add makefile and update documentation.
- **project**: Add Single-Exchange feature. Fix bug regarding the --key parameter not working by exporting the API key to environment variables and always checking there first, and if it is not present check the locally stored key.
- **project**: :construction: Add foundation for Single-Exchange mode.

### Fix

- **api**: :bug: Provide a list of allowed role titles to user and model roles to prevent client error.
- **project**: :bug: Fix issue where locally stored api key is always used even when user provided key is present.
- **project**: :ambulance: Make sure the key is not only present as an arg, but also make sure it is empty.
- **docs**: :memo: Move tips and tricks to gptcli's help command.

### Refactor

- **project**: :pencil2: Fix spelling mistakes and change option name.
- **api**: :recycle: Remove option to return None and fix spelling errors.
- **api**: Improve doc string, code readability, and fix the return type hint.
- **install**: Simplify the install process by moving strings to definitions.py.
- **chat**: Add variable type hint to model parameter.
- **project**: Remove deprecated and soon to be deprecated LLMs.
- **project**: Remove deprecated (or soon to be) LLMs.

## 0.15.0 (2024-06-03)

### Feat

- **cli**: Improve the CLI parser.

### Refactor

- **cli**: Place 'on' 'off' options to the bottom to make it easier to track.
- **project**: Make minor improvements.
- Improve documentation, type hinting, change methods names to something more concise.

## 0.14.0 (2024-05-31)

### Feat

- **project**: Add the option to select cli or chat mode, and make 'storage' and 'continue from last available' as options.
- **chat**: Add the new 'storage' and 'continue from last'  features to Chat, and refactor the in-chat commands.
- **message**: :sparkles: Many features been added:
- **project**: Add basic storage management functionality to store and extract messages to and from JSON files.

### Refactor

- **install**: Change 'messages' name to 'storage'.
- **api**: Use the new iterability feature of Messages.
- **project**: Add commonly used filepath to definitions.

## 0.13.0 (2024-05-13)

### Feat

- **project**: Add support for gpt-4o.
- **project**: Add variable and return types to project.
- **project**: Add support for GPT4 turbo. Also adjust the name of the gpt-3.5-turbo.

### Fix

- **ingest**: Fix log messages when checking file type.

### Refactor

- **project**: Fix errors outputted by mypy.
- **chat**: Refactor the context feature further.
- **chat**: Extract large chuck of logic that checks for file content and adding it to message.
- **api**: Make improvements by adding variable and renaming variables and add some initial tests.
- **project**: Rename OpenAIHelper to OpenAiHelper.
- **project**: Resolve circular import issues with message.py and api_helper.py.

## 0.12.0 (2024-05-09)

### Feat

- **chat**: Improve multiline and single line messages.
- **message**: Expand Message functionality.
- **project**: Completely revamp how Message and Messages work. Add minor improvements to File tpye checks. Remove unnecessary property variables from classes as they can be confusing when using them in the same class.

### Fix

- **message**: Remove what can be considered dead code.
- **chat**: Remove live token count from chat as it is too computationally expensive (slow).

### Refactor

- **project**: Remove unused profiles file.

## 0.11.0 (2024-05-03)

### Refactor

- **project**: Move KeyboardInterrupt and EOFError cases to a decorator.
- **ingest**: Add some checks for Text and PDF to make sure the files exist before performing operations.

## 0.10.0 (2024-04-26)

### Feat

- **project**: Add PDF support and extend Text file support by checking if it is indeed a text file.

### Fix

- **install**: Remove the install checks preformed at program launch and rely only on .install_succesful file being present.

### Refactor

- **chat**: Remove mutiline input from all chats and enabale it only for the Openai chat.

## 0.9.0 (2024-04-22)

### Feat

- **chat**: Add multiline support.

### Refactor

- **chat**: Extract multine line support to private method.
- **chat**: Move the related private methods closer together.

## 0.8.0 (2023-09-10)

### Feat

- **helper**: Add error information retrieved from server to logs.

## 0.7.1 (2023-09-07)

### Fix

- **project**: Remove funcionality for random id install and fix some erros in install test file.

### Refactor

- **project**: Run isort, pylint, and black formatter.
- **tests**: Remove script as the newer one will be the default execution method for tests.

## 0.7.0 (2023-08-31)

### Feat

- **tests**: Use Docker to execute the tests with pytest.

### Fix

- **tests**: Execute unit tests the same way that Docker will.
- **tests**: Resolve import issue.

## 0.6.0 (2023-08-29)

### Feat

- **project**: Add support for gpt-3.5-turbo-16k.

## 0.5.4 (2023-08-29)

### Fix

- **helper**: Handle case where response is None.

## 0.5.3 (2023-08-26)

### Fix

- **helper**: Fix issue where response is always None.

## 0.5.2 (2023-08-26)

### Fix

- **helper**: Fix error where we try to add a None object to messages.

## 0.5.1 (2023-08-11)

### Fix

- **helper**: Make exception logs more concise.

### Refactor

- **helper**: Remove custom error codes and fix log messages.

## 0.5.0 (2023-08-11)

### Feat

- **project**: Add version number to project package.
- **project**: This will allow to pass text from files to the OpenAI API as if it was part of a previous message. Allowing us to ask questions about it.
- **helper**: Improve pattern matching and replace info with warning.
- **helper**: Add logic for handling HTTP errors.

### Fix

- **project**: Prettify the help output.
- **project**: Ignore tests folder when building project.
- **helper**: Use module pathing rather than relative pathing.
- **chat**: Resolve issue where some keys other than the arrow keys are also bound to left and right movement.

## 0.4.1 (2023-07-15)

### Fix

- **chat**: Resolve issue where some keys other than the arrow keys are also bound to left and right movement.

## 0.4.0 (2023-07-15)

### Feat

- **project**: Apply version number bump in root toml and in _version.py on cz bump.

### Refactor

- **project**: Simplify printing the version number.

## 0.3.2 (2023-07-08)

### Fix

- **project**: :bug: Replace hardcoded version number.

## 0.3.1 (2023-07-08)

## 0.3.0 (2023-07-08)

## 0.2.0 (2023-07-08)

### Feat

- **helper**: :sparkles: Get version number as defined in project toml file.

## 0.1.0 (2023-07-08)

### Feat

- **project**: :heavy_plus_sign: Add versioning via commitizen
- **project**: add gptcli entrypoint
- **project**: Add comprehensive gitignore.
- **project**: :construction: Add initial setup.py version. Contains program entry point.
- add ability to select roles for user and LLM
- **chat|cli|main**: add option for turning context 'on' or 'off'
- **messages**: add Messages class
- **project**: enable context retainment for chats. Chat will now retain and use previous messages to send to API
- **chat**: allow use of multiple exit commands
- **chat**: add multiple exit commands
- **storage**: add more basic functionality
- **storage**: add way of storing messages
- **chat**: allow mid message exit via KeyboardInterrupt or EOFError using try catch
- **install**: mark install successful with file, the program should only be responsible upto the first successful install
- **chat**: add some in chat command functionality
- **project**: add streaming option + remove chat completion in favour of post request
- **project**: add streaming option + remove chat completion in favour of post request
- **profiles**: add some context and examples
- **profiles**: add profiles to project
- **messages**: add message store and read support
- **main**: pass key as parameter to Install
- **cli**: add key as optional argument
- **install**: expose install steps via install method
- **install**: add api key as property + load_api_key method
- **install**: add methods for installing locally
- **machine**: add failing test
- **install**: add machine specific install and config tools
- **cli**: organize log level options
- **cli**: add tpyes to argparse
- **cli**: add model version options
- add arrow key support, add log support
- get api key from local file
- add more gpt versions
- add basic cli foundation
- **cli**: add files for cli
- **pytest**: add pytestini file
- add time tracking
- **all**: add logging
- **main**: run OpenAI, get response, pass to TTS
- **openai**: add one question option
- **project**: add an easy way to run unit tests
- **project**: add black formatter rules
- **polly**: add method to generate polly client
- **polly**: make it only SSO compatible
- **openai**: rename file and add skeleton code
- **openai**: rename file and add skeleton code
- **docs**: add readme file

### Fix

- **SECURITY**: :lock: Update requests to patched version
- import from message
- **readme**: add tips and tricks section
- **install**: check for valid API key
- **cli**: turn on context by default
- **project**: ignore properties for docstrings
- **install**: make openai api key file only root accessible
- **README**: update the doc
- **README**: update the doc
- wrong placement of try except
- **api_helper**: catch ChunkedEncodingError
- **api_helper**: catch ChunkedEncodingError
- **README**: update chat example
- **api_helper**: catch keyboard interrupt && change message
- **api_helper**: catch keyboard interrupt && change message
- remove error catch, it is unknown if it needs to be handled
- **chat**: relabel the USER to MESSAGE and AI to REPLY
- **install**: bug where API key is not written to file when api setup is aborted
- **install**: display message after we enter an invalid value
- **chat**: prevent API key from leaking into Openai chat
- **docs**: update readme
- **docs**: update readme
- **docs**: update readme
- **openai_helper**: bug with expected code type
- **dependencies**: add requests
- **dependencies**: add dependency info
- **install**: remove unecessary API check
- **install**: use do while
- **cli**: for now, set stream on by default
- **openai_helper**: broken streaming issue
- **install**: log if API key is valid
- **chat**: fix syntax error
- **install**: correct where we create the messages folder
- **install**: always load API key to env
- **install**: perform install only if .gptcli not present
- **install**: big where valid key is overwritten with nothing
- **openai**: if key is in env then load to openai.api_key
- **install**: fix 404 error when 'correct' request made to api
- **install**: improve method
- **install**: improve method
- **install**: bug introduced by underscore
- **install**: make ask for api key part of standard install
- **install**: add method ask for api key if api is invalid
- **install**: add method to directly check api key is valid
- **install**: set default value for api key to str
- **install**: fix log names
- **install**: reduce token size from 100 to 10
- **test**: add create folders method
- **test**: add random id and use os.path.join
- **install**: use gpt-3.5 for faster replies
- **cli**: remove case transform lower
- **cli**: output stacktrace of errors in logs
- add readline, add boto3
- **cli**: add EOFerror and keyboard inter support
- update doc to reflect more recent changes
- update doc to reflect more recent changes
- update doc to reflect more recent changes
- don't allow empty strings
- cannot find src module- > mv main to root
- **logs**: building message, remove s
- **main**: print the response
- **pylint**: ignore all test_ files
- **logs**: use correct module name in logs
- **gitignore**: ignore mp3 files specifically
- **formatter**: cap line length at 120 not 200
- **gitignore**: ignore mp3 files

### Refactor

- :art: reorganize project structure in a gptcli folder
- add return types
- move code to dedicated methods
- **helper**: overwrite str and make dict a method
- **helper**: make gpt 3.5 default again as gpt 4 is expensive (20x)
- **helper**: fix imports of api helper
- **helper**: rename file
- make gpt4 the default
- **chat**: reply function for openai
- **chat**: GPTCLI messaging
- **polly**: add methods for more play options
