# How do I setup the project for development?
These steps assume your system's minimum Python version is the minimum indicate in the [README](./README.md), are using VSCode or PyCharm, and have already run the program in `chat` mode at least once with a valid API key. If you do not have at least the minimum Python version, it is recommended you install [homebrew](https://brew.sh/) and run `brew install python@3.11`; replace `3.11` with the latest project supported version.

With that being said, you may complete the following steps:  
[1] Install [`miniconda`](https://www.anaconda.com/docs/getting-started/miniconda/install).  
[2] Open a terminal in your preferred directory; something like `~/Documents/Git/mine/`.  
[3] Run `git clone https://github.com/deathbychocolate/gptcli.git`.  
[4] Run `cd gptcli`.  
[5] Run `make setup`.  
[6] Run `make install`.  
[7] Run `pipenv shell`.  
[8] Run `gptcli` or `python3 gptcli/main.py`.  
[9] Run `make test` and `make coverage`.  
[10] Run [./gptcli/main.py](./gptcli/main.py) with VSCode's or PyCharm's debug feature.

### Explanation:
[1] Miniconda sets up a default and always active virtual environment called `base`. This allows us to install packages without installing them system-wide; thus avoiding use of `pip install --break-system-packages`.

[5] Installs `python-dotenv`, `pipenv`, and `pre-commit` along with the rules in `.pre-commit-config`.

[6] Installs project dependencies, type stubs, and the project in an editable state, allowing us to run `gptcli` as a terminal command and dynamically adding changes from the source code.

[9] The first runs the tests using `pytest` and the second does the same but generates `coverage` html report as well in the project root. If both are generating only green output, it means the install process has been successful.

[10] The project requires passing certain default values to trigger `chat` and `se`. This is because debug mode "skips" over argparse creating the default values we usually pass down the program's pipeline. To streamline things, the configs needed have been added to [./vscode/launch.json](./.vscode/launch.json) and the `.idea` folder. To use the VSCode debug config, you must set the current active file in VSCode to be [./gptcli/main.py](./gptcli/main.py) by opening the file in a tab and clicking in that file with your cursor. Then you may select VSCode's built-in *Run and Debug* feature (left hand side, under *Explorer*) and click the green arrow with the `gptcli openai chat` option or any other. If you are using PyCharm, click the debug button near the top right of the application.

# How do I use the project's Makefile?
From the project root directory, run `make` or `make help` to display all Makefile targets documentation.  

It works because in the Makefile there we set the `.DEFAULT_GOAL` variable to execute the `help` target. This target is set to execute the [./scripts/help.sh](./scripts/help.sh) script against our Makefile.
