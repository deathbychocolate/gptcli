.DEFAULT_GOAL := help

MAKEFILE_PATH := $(shell readlink -f Makefile) ## Makefile absolute path.

.PHONY: install
install: ## Install project dependencies using pipenv.
	@pipenv install --dev
	@pipenv run mypy --install-types
	@pipenv run pip install --editable .

.PHONY: test
test: ## Run tests with pytest.
	@pipenv run pytest -x --log-cli-level=ERROR

.PHONY: coverage
test_coverage: ## Run tests with pytest and generate code coverage report (html).
	@pipenv run pytest -x --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html --cov-branch

.PHONY: clean
clean: ## Remove __pycache__ and cpython generated files (gptcli folder only).
	@-find . -type d -name "__pycache__" -exec rm -rf {} \;
	@-find . -type f -name "*.cpython-*" -exec rm -f {} \;

.PHONY: clean_coverage
clean_coverage: ## Remove coverage report and metadata.
	@-rm .coverage
	@-rm -r htmlcov

.PHONY: build_wheel
build_wheel: ## Run the 'build' module to generate a 'tar' and 'wheel' file in a 'dist' folder.
	@-rm dist/*
	@python3 -m build

.PHONY: help
help: ## Show help and exit.
	@./scripts/help.sh $(MAKEFILE_PATH)
