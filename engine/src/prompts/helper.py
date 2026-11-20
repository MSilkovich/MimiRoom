from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.schemas import Summary

_PROMPTS_DIR = Path(__file__).parent

_env = Environment(
    loader=FileSystemLoader(_PROMPTS_DIR),
    autoescape=select_autoescape(enabled_extensions=()),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_prompt(name: str = "system_prompt.md") -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def render_summary(ctx: "Summary") -> str:
    template = _env.get_template("summary.j2")
    return template.render(**ctx.model_dump()).strip()

EMPTY_SUMMARY = "Это неизвестный пользователь, о нем нет информации. Ты должен выяснить у него все обязательные данные для записи, а необязательные, если он их передаст - записать в формате {\"ключ\":\"значение\"} в поле optinons"