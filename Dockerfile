FROM python:latest

WORKDIR /app
COPY . /app

# Update and upgrade container packages
RUN apt update
RUN apt upgrade -y
RUN apt autoremove
RUN apt autoclean
RUN pip install --upgrade pip

# Install Rust so that pipenv functions
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install our app
RUN pip install pipenv
RUN pipenv install --system --deploy
