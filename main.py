#!/usr/bin/env python3
"""
This is the main file for the project
"""
import time
import logging

from src.main.ask_openai import AskOpenAI
from src.main.text_to_speech import TextToSpeech


logging.basicConfig(level=logging.INFO)


def main() -> None:
    """
    This is the main function
    """
    time_start = time.time()
    response = AskOpenAI(AskOpenAI.DEFAULT_ENGINE, "When did greece win the european football championship?").ask()
    time_end = time.time()
    time_taken = time_end - time_start
    logging.info("Time taken to generate text: %f", time_taken)

    time_start = time.time()
    text_to_speech = TextToSpeech(response)
    time_end = time.time()
    time_taken = time_end - time_start
    logging.info("Time taken to generate audio: %f", time_taken)

    text_to_speech.generate_and_play_audio_stream()


if __name__ == "__main__":
    main()
