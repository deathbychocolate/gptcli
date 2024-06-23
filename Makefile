install:
	pip install pipenv
	pipenv shell
	pipenv install --dev
	mypy --install-types
	pip install --editable .
	exit

test:
	pipenv run pytest --log-cli-level=ERROR

coverage:
	pipenv run pytest --log-cli-level=ERROR --cov=gptcli/src/ --cov-report html

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +

ccoverage:
	rm .coverage
	rm -r htmlcov