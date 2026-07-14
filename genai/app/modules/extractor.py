"""
Baseline-извлекатель атрибута + заготовка улучшенного.

Baseline: «текст → JSON», парсинг best-effort, БЕЗ грунтинга и без проверки уверенности.
Задача — extract_attribute_grounded: structured output + few-shot + грунтинг-фильтр
(source_quote обязан присутствовать в тексте, иначе value=None).
"""

import json
import re
from typing import cast

from pydantic import ValidationError

from app.config import DEFAULT_EXTRACTION_POLICY, ExtractionPolicy
from app.models import ExtractedValue as ExtractedValue
from app.models import LLMExtractionResponse
from app.modules.grounding import ground_response
from app.modules.registry import get_attribute
from app.prompts.extraction_prompts import (
    RETRY_INSTRUCTION,
    build_retry_user_prompt,
    build_system_prompt,
    build_user_prompt,
)
from app.utils.llm_client import CompletionClient, LLMClient

_FENCED_JSON_RE = re.compile(
    r"\A```(?:json)?[ \t]*(?:\r?\n)?(?P<payload>.*?)(?:\r?\n)?```[ \t]*\Z",
    flags=re.IGNORECASE | re.DOTALL,
)


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


def _parse_llm_response(raw: str) -> LLMExtractionResponse:
    """Разобрать строгий direct или целиком fenced JSON без вырезания из болтовни."""
    cleaned = raw.strip()
    fenced = _FENCED_JSON_RE.fullmatch(cleaned)
    payload = fenced.group("payload").strip() if fenced else cleaned
    return LLMExtractionResponse.model_validate_json(payload)


async def extract_attribute_baseline(
    text: str,
    attr_code: str,
    *,
    client: CompletionClient | None = None,
) -> ExtractedValue:
    """Текущий подход — доверяем модели как есть."""
    attr = get_attribute(attr_code)
    llm = client if client is not None else LLMClient()
    raw = await llm.complete(
        system="Извлеки значение атрибута. Верни JSON: value, unit, confidence, source_quote.",
        user=f"Атрибут: {attr.display_name}\nТекст: {text}",
    )
    data = _loose_json(raw) or {}
    payload = {key: data.get(key) for key in ("value", "unit", "confidence", "source_quote")}
    return ExtractedValue.model_validate(payload)


async def extract_attribute_grounded(
    text: str,
    attr_code: str,
    *,
    client: CompletionClient | None = None,
    policy: ExtractionPolicy = DEFAULT_EXTRACTION_POLICY,
) -> ExtractedValue:
    """Извлечь атрибут со строгим парсингом, bounded retry и grounding."""
    attribute = get_attribute(attr_code)
    llm = client if client is not None else LLMClient()
    system = build_system_prompt()
    original_user = build_user_prompt(text, attribute)
    attempt_user = original_user

    for attempt in range(policy.max_attempts):
        attempt_system = system if attempt == 0 else f"{system}\n\n{RETRY_INSTRUCTION}"
        raw = await llm.complete(system=attempt_system, user=attempt_user)
        try:
            response = _parse_llm_response(raw)
        except ValidationError as error:
            error_types = tuple(str(detail["type"]) for detail in error.errors())
            attempt_user = build_retry_user_prompt(original_user, raw, error_types)
            continue
        return ground_response(response, text, attribute, policy)

    return ExtractedValue(rejected_reason="invalid_model_response")
