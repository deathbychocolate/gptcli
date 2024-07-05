.PHONY: install
install:
	pip install pipenv
	pipenv shell
	pipenv install --dev
	mypy --install-types
	pip install --editable .
	exit

.PHONY: test
test:
	pipenv run pytest --log-cli-level=ERROR

.PHONY: coverage
coverage:
	pipenv run pytest --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html

.PHONY: clean
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +

.PHONY: clean-coverage
clean-coverage:
	rm .coverage
	rm -r htmlcov