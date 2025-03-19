.DEFAULT_GOAL := help

MAKEFILE_PATH := $(shell readlink -f Makefile) ## Makefile absolute path.


## Standard project targets.
.PHONY: install
install: has_pipenv ## Install project dependencies using pipenv.
	@pipenv install --dev
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
	@-find . -type d -name "__pycache__" -exec rm -rf {} \;
	@-find . -type f -name "*.cpython-*" -exec rm -f {} \;

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
