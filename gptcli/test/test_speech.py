"""
File that contains all tests related to TextToSpeech
"""

import boto3
import pytest

from gptcli.src.speech import TextToSpeech


def test_should_generate_and_store_audio_stream_to_file():
    assert False
    # generate_and_store_audio_stream_to_file() -> str:


def test_should_generate_and_play_audio_stream():
    assert False
    # generate_and_play_audio_stream() -> None:


def test_should__generate_audio_stream():
    assert False
    # _generate_audio_stream() -> bytes:


def test_should__generate_polly_client():
    assert False
    # _generate_polly_client() -> boto3.client:


def test_should__store_audio_stream_to_file():
    assert False
    # _store_audio_stream_to_file(, stream: bytes) -> str:


def test_should__generate_file_name():
    assert False
    # _generate_file_name() -> str:


def test_should_write_audio_to_file():
    assert False
    # write_audio_to_file(, filename: str, stream: bytes) -> None:


def test_should_play_audio_stream():
    assert False
    # play_audio_stream(, stream: bytes) -> None:


def test_should_play_audio_file():
    assert False
    # play_audio_file(, filename: str) -> None:
