#!/usr/bin/env python3
"""
This is the main file for the project
"""
from src.main.polly import TextToSpeech

def main() -> None:
    """
    This is the main function
    """
    text_to_speech = TextToSpeech("This is a test. Test test test.")
    file_path = text_to_speech.generate_and_store_audio_file()
    text_to_speech.play_audio_file(f"{file_path}")


if __name__ == "__main__":
    main()
