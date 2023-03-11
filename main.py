#!/usr/bin/env python3
"""
This is the main file for the project
"""
from src.main.text_to_speech import TextToSpeech


def main() -> None:
    """
    This is the main function
    """
    text_to_speech = TextToSpeech("This is a test. Test test test.")
    text_to_speech.generate_and_play_audio_stream()


if __name__ == "__main__":
    main()
