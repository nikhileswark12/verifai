import os
from typing import Dict

from app.services.exceptions import PromptNotFoundError

_PROMPT_CACHE: Dict[str, str] = {}


def load_prompt(name: str) -> str:
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "..", "prompts", f"{name}.md")
    prompt_path = os.path.normpath(prompt_path)

    if not os.path.exists(prompt_path):
        raise PromptNotFoundError(f"Prompt '{name}' not found at {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as file:
        content = file.read()

    _PROMPT_CACHE[name] = content
    return content
