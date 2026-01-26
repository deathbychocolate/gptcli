.DEFAULT_GOAL := help

MAKEFILE_PATH := $(shell readlink -f Makefile)## Makefile absolute path.


## Standard project targets.
.PHONY: setup
setup: ## Setup pre-commit hooks.
	@pip install -U pre-commit
	@pre-commit install --install-hooks --overwrite

.PHONY: install
install: ## Install project dependencies using uv.
	@uv sync
	@uv run mypy --install-types --non-interactive

.PHONY: test
test: ## Run tests with pytest.
	@uv run pytest -x --log-cli-level=ERROR

.PHONY: test_nox
test_nox: ## Run tests with pytest on all supported Python versions.
	@uv run nox --session test

.PHONY: coverage
coverage: ## Run tests with pytest and generate code coverage report (html).
	@uv run pytest -x --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html --cov-branch

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
	@uv run python -m build


## Custom scripts to optimize Makefile.
.PHONY: help
help: ## Show help and exit.
	@./scripts/help.sh $(MAKEFILE_PATH)
