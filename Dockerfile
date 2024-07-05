FROM python:latest

WORKDIR /gptcli
COPY . /gptcli

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

# https://stackoverflow.com/questions/67763121/installing-pyaudio-to-docker-container
# https://stackoverflow.com/questions/38480029/libsndfile-so-1-cannot-open-shared-object-file-no-such-file-or-directory
# RUN apt install libsndfile1 -y
# RUN apt install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y
