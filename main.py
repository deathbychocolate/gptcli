#!/usr/bin/env python3
"""
This is the main file for the project
"""
# import time
# import logging

# from src.main.openai_helper import OpenAIHelper
# from src.main.text_to_speech import TextToSpeech
from src.main.cli import CommandLineInterface


def main() -> None:
    """
    This is the main function
    """
    cli = CommandLineInterface()
    cli.parse()
    cli.run()
    # time_start = time.time()
    # time_end = time.time()
    # time_taken = time_end - time_start
    # logger.info("Time taken to generate text: %f", time_taken)

    # time_start = time.time()
    # text_to_speech = TextToSpeech(response)
    # time_end = time.time()
    # time_taken = time_end - time_start
    # logger.info("Time taken to generate audio: %f", time_taken)

    # text_to_speech.generate_and_play_audio_stream()


if __name__ == "__main__":
    main()
