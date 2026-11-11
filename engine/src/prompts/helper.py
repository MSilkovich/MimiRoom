from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str = "system_prompt.md") -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")
