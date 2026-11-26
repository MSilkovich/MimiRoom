"""Экранирование и нормализация текста для Telegram MarkdownV2.

Telegram требует экранировать служебные символы MarkdownV2::

    _ * [ ] ( ) ~ ` > # + - = | { } . !

LLM при этом отдаёт обычный Markdown: заголовки ``#``, таблицы с ``|``,
горизонтальные линии ``---``, цитаты ``>``, ``**жирный**`` и т.п.
MarkdownV2 **не поддерживает заголовки и таблицы**, а неэкранированные
символы приводят к ``Bad Request: can't parse entities``.

Поэтому здесь:

- :func:`escape_md_v2` — полностью экранирует текст (без разметки);
- :func:`to_markdown_v2` — приводит «человеческий» Markdown к тому виду,
  который Telegram реально умеет рисовать: заголовки → жирный, таблицы →
  список, ``---`` → разделитель, цитаты → blockquote, списки → ``•``;
- :func:`mention_md_v2` — упоминание пользователя в формате MarkdownV2.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import User

# Полный набор служебных символов MarkdownV2.
_SPECIAL = r"_*\[\]()~`>#+\-=|{}.!\\"
_SPECIAL_SET = frozenset("_*[]()~`>#+-=|{}.!\\")
_ESCAPE_RE = re.compile(r"([" + _SPECIAL + r"])")

# Inline-конструкции.
_LINK_RE = re.compile(r"\[([^\]\n]*)\]\(([^)\s]+)\)")
_LINK_ANGLE_RE = re.compile(r"\[([^\]\n]*)\]\(\s*<([^>\n]*)>\s*\)")
_VALID_URL_RE = re.compile(r"^(?:https?://|tg://|mailto:)")
_HTML_BR_RE = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)
_HTML_PRE_RE = re.compile(
    r"<\s*pre\s*>(.*?)<\s*/\s*pre\s*>", re.IGNORECASE | re.DOTALL
)
_HTML_CODE_RE = re.compile(
    r"<\s*code\s*>(.*?)<\s*/\s*code\s*>", re.IGNORECASE | re.DOTALL
)
_HTML_LINK_RE = re.compile(
    r'<\s*a\s+href\s*=\s*["\']([^"\']*)["\']\s*>(.*?)<\s*/\s*a\s*>',
    re.IGNORECASE | re.DOTALL,
)
_HTML_FORMAT_RES = (
    (
        re.compile(r"<\s*(b|strong)\s*>(.*?)<\s*/\s*\1\s*>",
                   re.IGNORECASE | re.DOTALL),
        "*",
        "*",
    ),
    (
        re.compile(r"<\s*(i|em)\s*>(.*?)<\s*/\s*\1\s*>",
                   re.IGNORECASE | re.DOTALL),
        "_",
        "_",
    ),
    (
        re.compile(r"<\s*(u|ins)\s*>(.*?)<\s*/\s*\1\s*>",
                   re.IGNORECASE | re.DOTALL),
        "__",
        "__",
    ),
    (
        re.compile(r"<\s*(s|strike|del)\s*>(.*?)<\s*/\s*\1\s*>",
                   re.IGNORECASE | re.DOTALL),
        "~",
        "~",
    ),
)

# Блочные конструкции Markdown.
_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
_TABLE_SEP_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
_INDEX_HEADERS = {"№", "#", "n", "no", "no.", "п/п"}


def escape_md_v2(text: str) -> str:
    """Экранировать все служебные символы MarkdownV2."""
    if not text:
        return text
    return _ESCAPE_RE.sub(r"\\\1", text)


def _escape_code(text: str) -> str:
    """Экранировать текст внутри ``code``/``pre``."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _escape_url(url: str) -> str:
    """Экранировать URL внутри MarkdownV2-ссылки."""
    return url.replace("\\", "\\\\").replace(")", "\\)")


def mention_md_v2(user: "User") -> str:
    """Упоминание пользователя, безопасное для MarkdownV2."""
    name = escape_md_v2(user.full_name or str(user.id))
    return f"[{name}](tg://user?id={user.id})"


def _match_html(text: str, index: int) -> tuple[str, int] | None:
    """Преобразовать простой HTML-тег в MarkdownV2 (если он здесь)."""
    match = _HTML_BR_RE.match(text, index)
    if match:
        return "\n", match.end()

    match = _HTML_PRE_RE.match(text, index)
    if match:
        return f"```{_escape_code(match.group(1))}```", match.end()

    match = _HTML_CODE_RE.match(text, index)
    if match:
        return f"`{_escape_code(match.group(1))}`", match.end()

    match = _HTML_LINK_RE.match(text, index)
    if match:
        url, label = match.group(1), match.group(2)
        return f"[{_inline_md_v2(label)}]({_escape_url(url)})", match.end()

    for regex, open_marker, close_marker in _HTML_FORMAT_RES:
        match = regex.match(text, index)
        if match:
            inner = _inline_md_v2(match.group(2))
            return f"{open_marker}{inner}{close_marker}", match.end()

    return None


def _inline_md_v2(text: str) -> str:
    """Экранировать/нормализовать одну строку (inline-разметка)."""
    if not text:
        return text

    out: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        char = text[i]

        # Блок кода ```...``` (в inline-контексте тоже встречается)
        if text.startswith("```", i):
            end = text.find("```", i + 3)
            if end != -1:
                out.append("```")
                out.append(_escape_code(text[i + 3:end]))
                out.append("```")
                i = end + 3
                continue
            out.append("\\`\\`\\`")
            i += 3
            continue

        # Инлайн-код `...`
        if char == "`":
            end = text.find("`", i + 1)
            if end > i + 1 and "\n" not in text[i + 1:end]:
                out.append("`")
                out.append(_escape_code(text[i + 1:end]))
                out.append("`")
                i = end + 1
                continue
            out.append("\\`")
            i += 1
            continue

        # Ссылка [текст](url)
        if char == "[":
            match = _LINK_RE.match(text, i)
            if match and _VALID_URL_RE.match(match.group(2)):
                label = _inline_md_v2(match.group(1))
                out.append(f"[{label}]({_escape_url(match.group(2))})")
                i = match.end()
                continue

            angle = _LINK_ANGLE_RE.match(text, i)
            if angle:
                label, url = angle.group(1), angle.group(2).strip()
                if _VALID_URL_RE.match(url):
                    out.append(f"[{_inline_md_v2(label)}]({_escape_url(url)})")
                else:
                    # URL-заглушка из промпта (<ссылка ...>) — только текст.
                    out.append(_inline_md_v2(label))
                i = angle.end()
                continue

        # **жирный**
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end > i + 2:
                out.append("*")
                out.append(_inline_md_v2(text[i + 2:end]))
                out.append("*")
                i = end + 2
                continue

        # __жирный__
        if text.startswith("__", i):
            end = text.find("__", i + 2)
            if end > i + 2:
                out.append("*")
                out.append(_inline_md_v2(text[i + 2:end]))
                out.append("*")
                i = end + 2
                continue

        # ~~зачёркнутый~~
        if text.startswith("~~", i):
            end = text.find("~~", i + 2)
            if end > i + 2:
                out.append("~")
                out.append(_inline_md_v2(text[i + 2:end]))
                out.append("~")
                i = end + 2
                continue

        # *курсив* (не путать со списком "* пункт")
        if char == "*":
            if i + 1 < n and not text[i + 1].isspace():
                end = text.find("*", i + 1)
                if (
                    end > i + 1
                    and "\n" not in text[i + 1:end]
                    and not text[end - 1].isspace()
                ):
                    out.append("_")
                    out.append(_inline_md_v2(text[i + 1:end]))
                    out.append("_")
                    i = end + 1
                    continue

        # _курсив_ (не трогаем snake_case)
        if char == "_":
            prev_ok = i == 0 or not text[i - 1].isalnum()
            if prev_ok and i + 1 < n and not text[i + 1].isspace():
                end = text.find("_", i + 1)
                if (
                    end > i + 1
                    and "\n" not in text[i + 1:end]
                    and not text[end - 1].isspace()
                    and (end + 1 >= n or not text[end + 1].isalnum())
                ):
                    out.append("_")
                    out.append(_inline_md_v2(text[i + 1:end]))
                    out.append("_")
                    i = end + 1
                    continue

        # Уже экранированный символ — оставляем как есть.
        if char == "\\" and i + 1 < n and text[i + 1] in _SPECIAL_SET:
            out.append(text[i:i + 2])
            i += 2
            continue

        # Простые HTML-теги -> MarkdownV2.
        if char == "<":
            rendered = _match_html(text, i)
            if rendered is not None:
                value, i = rendered
                out.append(value)
                continue

        # Обычный символ.
        if char in _SPECIAL_SET:
            out.append("\\" + char)
        else:
            out.append(char)
        i += 1

    return "".join(out)


def _split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _render_table(lines: list[str], start: int) -> tuple[list[str], int]:
    """Превратить Markdown-таблицу в аккуратный список для Telegram."""
    header = _split_table_row(lines[start])
    skip = 0
    if header and header[0].strip().lower() in _INDEX_HEADERS:
        skip = 1

    rendered: list[str] = []
    index = start + 2  # пропускаем заголовок и линию-разделитель
    while index < len(lines) and "|" in lines[index] and lines[index].strip():
        cells = _split_table_row(lines[index])[skip:]
        values = [_inline_md_v2(cell) for cell in cells if cell]
        if values:
            rendered.append("• " + " — ".join(values))
        index += 1

    return rendered, index


def _to_markdown_v2(text: str) -> str:
    """Блочная нормализация Markdown -> MarkdownV2."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Блок кода: не трогаем внутренности построчно.
        if line.lstrip().startswith("```"):
            block = [line]
            j = i + 1
            closed = False
            while j < n:
                block.append(lines[j])
                if lines[j].lstrip().startswith("```"):
                    closed = True
                    j += 1
                    break
                j += 1
            out.append(_inline_md_v2("\n".join(block)))
            i = j if closed else n
            continue

        # Таблица с разделителем во второй строке.
        if (
            "|" in line
            and i + 1 < n
            and _TABLE_SEP_RE.match(lines[i + 1])
        ):
            table, i = _render_table(lines, i)
            out.extend(table)
            continue

        # Заголовок ## -> жирный.
        heading = _HEADING_RE.match(line)
        if heading:
            content = _inline_md_v2(heading.group(2))
            out.append(f"*{content}*" if content else "")
            i += 1
            continue

        # Горизонтальная линия --- -> визуальный разделитель.
        if _HR_RE.match(line):
            out.append("────────────")
            i += 1
            continue

        # Цитата > -> blockquote MarkdownV2.
        quote = _QUOTE_RE.match(line)
        if quote:
            out.append("> " + _inline_md_v2(quote.group(1)))
            i += 1
            continue

        # Ненумерованный список -> •.
        item = _UL_RE.match(line)
        if item:
            out.append("• " + _inline_md_v2(item.group(1)))
            i += 1
            continue

        # Нумерованный список -> 1. (точка экранируется).
        item = _OL_RE.match(line)
        if item:
            out.append(f"{item.group(1)}\\. " + _inline_md_v2(item.group(2)))
            i += 1
            continue

        out.append(_inline_md_v2(line))
        i += 1

    return "\n".join(out)


def to_markdown_v2(text: str) -> str:
    """Привести произвольный Markdown/HTML к валидному Telegram MarkdownV2.

    Поддерживает заголовки, таблицы, списки, цитаты, горизонтальные линии,
    базовую inline-разметку и простые HTML-теги. Всё остальное экранируется.
    """
    if not text:
        return text
    return _to_markdown_v2(text)
