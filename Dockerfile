FROM python:3.11-slim-buster

WORKDIR /app
COPY . /app

# Update and upgrade container packages
RUN apt update && apt upgrade -y && apt autoremove && apt autoclean
RUN pip install --upgrade pip

# Remove high risk vulnerability in setuptools
RUN pip install -U setuptools

# Install uv
RUN pip install uv

# Install our app
RUN uv sync --frozen --no-dev
RUN uv pip install --system -e .
