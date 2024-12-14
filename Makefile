.DEFAULT_GOAL := help

MAKEFILE_PATH := $(shell readlink -f Makefile) ## Makefile absolute path.

.PHONY: install
install: ## Install project dependencies using pipenv.
	@pipenv install --dev
	@mypy --install-types
	@pip install --editable .
	@exit

.PHONY: test
test: ## Run tests with pytest.
	@pipenv run pytest --log-cli-level=ERROR

.PHONY: coverage
test_coverage: ## Run tests with pytest and generate code coverage report (html).
	@pipenv run pytest --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html --cov-branch

.PHONY: clean
clean: ## Remove __pycache__ and cpython generated files (gptcli folder only).
	@find . -type d -name "__pycache__" -exec rm -rf {} \;
	@find . -type f -name "*.cpython-*" -exec rm -f {} \;

.PHONY: clean-coverage
clean_coverage: ## Remove coverage report and metadata.
	@rm .coverage
	@rm -r htmlcov

.PHONY: help
help: ## Show help and exit.
	@./scripts/help.sh $(MAKEFILE_PATH)
