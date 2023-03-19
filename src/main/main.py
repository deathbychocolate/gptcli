#!/usr/bin/env python3
"""
This is the main file for the project
"""
import time
import logging

from src.main.openai_helper import OpenAIHelper
# from src.main.text_to_speech import TextToSpeech


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    This is the main function
    """
    time_start = time.time()
    response = OpenAIHelper(OpenAIHelper.DEFAULT_ENGINE, "Πρότεινέ μου ελληνικά 5 βιβλία πέρι την ελληνική μυθολογία").send()
    time_end = time.time()
    time_taken = time_end - time_start
    logger.info("Time taken to generate text: %f", time_taken)
    print(response)

    # time_start = time.time()
    # text_to_speech = TextToSpeech(response)
    # time_end = time.time()
    # time_taken = time_end - time_start
    # logger.info("Time taken to generate audio: %f", time_taken)

    # text_to_speech.generate_and_play_audio_stream()


if __name__ == "__main__":
    main()
