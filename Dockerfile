FROM python:3.11-slim-buster

WORKDIR /app
COPY . /app

# Update and upgrade container packages
RUN apt update && apt upgrade -y && apt autoremove && apt autoclean
RUN pip install --upgrade pip

# Remove high risk vulnerability in setuptools
RUN pip install -U setuptools

# Install Rust so that pipenv functions
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install pipenv

# Install our app
RUN pipenv install --system --deploy
RUN pip install --editable .
