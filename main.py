#!/usr/bin/env python3
"""
This is the main file for the project
"""
from src.main.ask_openai import AskOpenAI
from src.main.text_to_speech import TextToSpeech


def main() -> None:
    """
    This is the main function
    """
    response = AskOpenAI(AskOpenAI.DEFAULT_ENGINE, "When did greece win the european football championship?").ask()
    text_to_speech = TextToSpeech(response)
    text_to_speech.generate_and_play_audio_stream()


if __name__ == "__main__":
    main()
