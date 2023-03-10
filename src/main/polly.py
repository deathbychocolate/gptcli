"""
This file contains the TextToSpeech class
"""
import io
import os
import time
import soundfile
import sounddevice
import boto3


class TextToSpeech:
    """
    This class is used to convert text to speech
    """

    def __init__(self, input_text: str) -> None:
        self.input_text = input_text

    def generate_and_store_audio_file(self) -> str:
        """
        Generate and store audio file to local file system

        :returns: The full path of the audio file
        """
        stream = self._generate_audio_stream()
        full_path = self._store_audio_file(stream)

        return full_path

    def generate_and_play_audio_stream(self) -> None:
        """
        Generate and play audio stream without storing to local file system

        :returns: None
        """
        stream = self._generate_audio_stream()
        self.play_audio_stream(stream)

    def _generate_audio_stream(self) -> bytes:
        """
        This method is used to convert text to speech

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

        return stream

    def _store_audio_file(self, stream: bytes) -> str:
        """
        This method is used to store the audio stream

        :param stream: The audio stream
        :returns: The full path of the audio file
        """
        filename = self._generate_file_name()
        self.write_audio_to_file(filename, stream)

        return filename

    def _generate_file_name(self) -> str:
        """
        This method is used to generate a file name

        :returns: The filename
        """
        path = ""  # "./audio/"
        filename = f"{int(time.time())}.mp3"
        file_path = "".join([path, filename])
        return file_path

    def _generate_polly_client(self) -> boto3.client:
        """
        This method is used to generate a boto3 client

        :returns: Polly client
        """
        aws_sso_profile_name = os.getenv("AWS_SSO_PROFILE_NAME", "Spark_Drop_Playground")
        client = boto3.session.Session(profile_name=aws_sso_profile_name).client("polly")

        return client

    def write_audio_to_file(self, filename: str, stream: bytes) -> None:
        """
        This method is used to write the audio stream to a file

        :param filename: The filename of the audio file
        :param stream: The audio stream
        :returns: None
        """
        data_io = io.BytesIO(stream)
        audio_data, frequency = soundfile.read(data_io, dtype="float64")
        soundfile.write(filename, audio_data, samplerate=frequency)

    def play_audio_file(self, filename: str) -> None:
        """
        This method is used to play the audio file

        :param filename: The filename of the audio file
        :returns: None
        """
        audio_data, sample_rate = soundfile.read(filename, dtype="float64")
        sounddevice.play(audio_data, samplerate=sample_rate)
        sounddevice.wait()

    def play_audio_stream(self, stream: bytes) -> None:
        """
        This method is used to play the audio stream

        :param stream: The audio stream
        :returns: None
        """
        data_io = io.BytesIO(stream)
        audio_data, frequency = soundfile.read(data_io, dtype="float64")
        sounddevice.play(audio_data, samplerate=frequency)
        sounddevice.wait()
