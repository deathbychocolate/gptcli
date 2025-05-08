"""Contains models supported by GPTCLI."""

openai: dict[str, str] = {
    # see here: https://platform.openai.com/docs/models/
    "GPT_3_5_TURBO": "gpt-3.5-turbo",
    "GPT_4": "gpt-4",
    "GPT_4_TURBO": "gpt-4-turbo",
    "GPT_4_1": "gpt-4.1",
    "GPT_4_1_MINI": "gpt-4.1-mini",
    "GPT_4O": "gpt-4o",
    "GPT_4O_MINI": "gpt-4o-mini",
    "O1": "o1",
    "O1_MINI": "o1-mini",
    "O1_PREVIEW": "o1-preview",
    "O1": "o1",
    "O3_MINI": "o3-mini",
    "O3": "o3",
    "O4_MINI": "o4-mini",
}

roles: list[str] = [
    "system",
    "assistant",
    "user",
    "function",
    "tool",
]

output_types: dict[str, str] = {
    "plain": "plain",
    "choices": "choices",
    "all": "all",
}
