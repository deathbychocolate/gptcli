"""
This file contains the TextToSpeech class
"""

import io
import logging
import os
import time
from logging import Logger

import boto3
import sounddevice
import soundfile

logger: Logger = logging.getLogger(__name__)


class TextToSpeech:
    """This class is used to convert text to speech"""

    def __init__(self, input_text: str) -> None:
        self.input_text = input_text

    def generate_and_store_audio_stream_to_file(self) -> str:
        """Generate and store audio stream to local file system

        :returns: The full path of the audio file
        """
        logger.info("Generating and storing audio stream")
        stream = self._generate_audio_stream()
        full_path = self._store_audio_stream_to_file(stream)

        return full_path

    def generate_and_play_audio_stream(self) -> None:
        """Generate and play audio stream without storing to local file system

        :returns: None
        """
        logger.info("Generating and playing audio stream")
        stream = self._generate_audio_stream()
        self.play_audio_stream(stream)

    def _generate_audio_stream(self) -> bytes:
        """This method is used to convert text to speech

        :returns: The audio stream
        """
        client = self._generate_polly_client()
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly/client/synthesize_speech.html
        response = client.synthesize_speech(
            Engine="neural",
            OutputFormat="mp3",
            SampleRate="24000",
            Text=self.input_text,
            TextType="text",
            VoiceId="Joanna",
        )

        stream = response["AudioStream"].read()
        logger.info("Audio stream generated")

        return stream

    def _generate_polly_client(self) -> boto3.client:
        """This method is used to generate a boto3 client

        :returns: Polly client
        """
        logger.info("Generating polly client")
        aws_sso_profile_name = os.getenv("AWS_SSO_PROFILE_NAME", "Spark_Drop_Playground")
        client = boto3.session.Session(profile_name=aws_sso_profile_name).client("polly")

        return client

    def _store_audio_stream_to_file(self, stream: bytes) -> str:
        """This method is used to store the audio stream

        :param stream: The audio stream
        :returns: The full path of the audio file
        """
        logger.info("Storing audio stream")
        filename = self._generate_file_name()
        self.write_audio_to_file(filename, stream)

        return filename

    def _generate_file_name(self) -> str:
        """This method is used to generate a file name

        :returns: The filename
        """
        path = ""  # "./audio/"
        filename = f"{int(time.time())}.mp3"
        file_path = "".join([path, filename])
        return file_path

    def write_audio_to_file(self, filename: str, stream: bytes) -> None:
        """This method is used to write the audio stream to a file

        :param filename: The filename of the audio file
        :param stream: The audio stream
        :returns: None
        """
        logger.info("Writing audio stream to file: %s", filename)
        data_io = io.BytesIO(stream)
        audio_data, frequency = soundfile.read(data_io, dtype="float64")
        soundfile.write(filename, audio_data, samplerate=frequency)

    def play_audio_stream(self, stream: bytes) -> None:
        """This method is used to play the audio stream

        :param stream: The audio stream
        :returns: None
        """
        logger.info("Playing audio stream")
        data_io = io.BytesIO(stream)
        audio_data, frequency = soundfile.read(data_io, dtype="float64")
        sounddevice.play(audio_data, samplerate=frequency)
        sounddevice.wait()

    def play_audio_file(self, filename: str) -> None:
        """This method is used to play the audio file

        :param filename: The filename of the audio file
        :returns: None
        """
        logger.info("Playing audio file: %s", filename)
        audio_data, sample_rate = soundfile.read(filename, dtype="float64")
        sounddevice.play(audio_data, samplerate=sample_rate)
        sounddevice.wait()
