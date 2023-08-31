FROM python:latest

WORKDIR /Users/username/

COPY . .
RUN python3 -m pip install pipenv
RUN python3 -m pipenv install --dev

# Update and upgrade container linux packages
RUN apt update
RUN apt upgrade -y

# https://stackoverflow.com/questions/67763121/installing-pyaudio-to-docker-container
# https://stackoverflow.com/questions/38480029/libsndfile-so-1-cannot-open-shared-object-file-no-such-file-or-directory
RUN apt install libsndfile1 -y
RUN apt install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y

CMD ["python3", "-m", "pipenv", "run", "pytest"]
