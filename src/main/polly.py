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
        This method is used to convert text to speech

        :returns: The filename of the audio file
        """
        aws_account_id = os.getenv("AWS_ACCOUNT_ID", "562832330937")
        aws_account_role = os.getenv("AWS_ACCOUNT_ROLE", "EngineeringAdmin")
        aws_region_name = os.getenv("AWS_REGION_NAME", "eu-west-1")

        profile_name = f"{aws_account_id}_{aws_account_role}"

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/polly/client/synthesize_speech.html
        response = (
            boto3.session.Session(
                profile_name=profile_name,
                region_name=aws_region_name,
            )
            .client("polly")
            .synthesize_speech(
                Engine="neural",
                OutputFormat="mp3",
                SampleRate="24000",
                Text=self.input_text,
                TextType="text",
                VoiceId="Joanna",
            )
        )

        # play the audio stream
        stream = response["AudioStream"].read()
        self.play_audio_stream(stream)

        # write the audio stream to a file
        filename = self.generate_file_name()
        self.write_audio_to_file(filename, stream)

        return filename

    def generate_file_name(self) -> str:
        """
        This method is used to generate a file name

        :returns: The filename
        """
        path = "./audio/"
        filename = f"{int(time.time())}.mp3"
        file_path = "".join([path, filename])
        return file_path

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
