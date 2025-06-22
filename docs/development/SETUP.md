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
