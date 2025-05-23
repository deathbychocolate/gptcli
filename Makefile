.DEFAULT_GOAL := help

MAKEFILE_PATH := $(shell readlink -f Makefile)## Makefile absolute path.


## Standard project targets.
.PHONY: dotenv
dotenv: ## Install python-dotenv (used for target 'setup').
	@pip install -U python-dotenv

.PHONY: setup
setup: dotenv ## Setup pre-commit and pipenv.
	@python3 -c "import os;import dotenv;dotenv.load_dotenv();assert os.environ['DBC_GPTCLI_SETUP_COMPLETE'] == '0', 'Your targets are already setup. To force a retry, change DBC_GPTCLI_SETUP_COMPLETE in .env from 1 to 0.'"
	@pip install -U pipenv
	@pip install -U pre-commit
	@pre-commit install --install-hooks --overwrite
	@python3 -c "import dotenv;dotenv.set_key(dotenv.find_dotenv(), 'DBC_GPTCLI_SETUP_COMPLETE', '1')"

.PHONY: install
install: has_pipenv ## Install project dependencies and the project (locally) using pipenv.
	@pipenv sync --dev
	@pipenv run mypy --install-types
	@pipenv run pip install --editable .

.PHONY: test
test: has_pipenv ## Run tests with pytest.
	@pipenv run pytest -x --log-cli-level=ERROR

.PHONY: coverage
coverage: has_pipenv ## Run tests with pytest and generate code coverage report (html).
	@pipenv run pytest -x --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html --cov-branch

.PHONY: clean
clean: ## Remove __pycache__ and cpython generated files (gptcli folder only).
	@-find . -type d -name "__pycache__" -exec rm -rf {} \; 2> /dev/null
	@-find . -type f -name "*.cpython-*" -exec rm -f {} \; 2> /dev/null

.PHONY: clean_coverage
clean_coverage: ## Remove coverage report and metadata.
	@-rm .coverage
	@-rm -r htmlcov

.PHONY: build
build: ## Run the 'build' module to generate a 'tar' and 'wheel' file in a 'dist' folder.
	@-rm dist/*
	@python3 -m build


## Custom scripts to optimize Makefile.
.PHONY: has_pipenv
has_pipenv:
	@echo "Checking for pipenv in PATH."
	@./scripts/has_pipenv.sh

.PHONY: help
help: ## Show help and exit.
	@./scripts/help.sh $(MAKEFILE_PATH)
