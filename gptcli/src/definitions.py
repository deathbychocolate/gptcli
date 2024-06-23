"""Contains models supported by GPTCLI."""

openai: dict = {
    # see here: https://platform.openai.com/docs/models/
    "GPT_3_5_TURBO": "gpt-3.5-turbo",
    "GPT_4": "gpt-4",
    "GPT_4_TURBO": "gpt-4-turbo",
    "GPT_4O": "gpt-4o",
}

roles: list = [
    "system",
    "assistant",
    "user",
    "function",
    "tool",
]

extraction_types: dict = {
    "plain": "plain",
    "choices": "choices",
    "all": "all",
}
