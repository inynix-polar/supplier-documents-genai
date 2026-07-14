"""
Baseline-извлекатель атрибута + заготовка улучшенного.

Baseline: «текст → JSON», парсинг best-effort, БЕЗ грунтинга и без проверки уверенности.
Задача — extract_attribute_grounded: structured output + few-shot + грунтинг-фильтр
(source_quote обязан присутствовать в тексте, иначе value=None).
"""

import json
import re
from typing import cast

from pydantic import BaseModel

from app.modules.registry import get_attribute
from app.utils.llm_client import LLMClient


class ExtractedValue(BaseModel):
    value: str | None = None
    unit: str | None = None
    confidence: str | None = None  # high | medium | low
    source_quote: str | None = None
    rejected_reason: str | None = None  # почему отбраковано (для грунтинг-фильтра)


def _loose_json(raw: str) -> dict[str, object] | None:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        parsed: object = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        return None
    return cast(dict[str, object], parsed)


async def extract_attribute_baseline(text: str, attr_code: str) -> ExtractedValue:
    """Текущий подход — доверяем модели как есть."""
    attr = get_attribute(attr_code)
    llm = LLMClient()
    raw = await llm.complete(
        system="Извлеки значение атрибута. Верни JSON: value, unit, confidence, source_quote.",
        user=f"Атрибут: {attr.display_name}\nТекст: {text}",
    )
    data = _loose_json(raw) or {}
    payload = {key: data.get(key) for key in ("value", "unit", "confidence", "source_quote")}
    return ExtractedValue.model_validate(payload)


async def extract_attribute_grounded(text: str, attr_code: str) -> ExtractedValue:
    """
    TODO(кандидат):
      - few-shot промпт (вынести в app/prompts/), structured output;
      - устойчивый парсинг + осмысленный retry;
      - ГРУНТИНГ: если source_quote отсутствует в тексте — value=None + rejected_reason.
    """
    raise NotImplementedError
