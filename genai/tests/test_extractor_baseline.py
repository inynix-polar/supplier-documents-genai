"""Контрактные тесты baseline-извлекателя."""

import pytest

from app.modules.extractor import ExtractedValue, _loose_json, extract_attribute_baseline
from app.utils.llm_client import LLMClient


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"value": "100"}', {"value": "100"}),
        ('```json\n{"value": "100"}\n```', {"value": "100"}),
    ],
)
def test_loose_json_parses_supported_formats(
    raw: str,
    expected: dict[str, object],
) -> None:
    assert _loose_json(raw) == expected


@pytest.mark.parametrize("raw", ["not-json", "[]", '"value"'])
def test_loose_json_rejects_invalid_payload(raw: str) -> None:
    assert _loose_json(raw) is None


@pytest.mark.asyncio
async def test_baseline_maps_llm_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_complete(_self: LLMClient, system: str, user: str) -> str:
        assert "Верни JSON" in system
        assert "Номинальный диаметр" in user
        return (
            '```json\n{"value": "100", "unit": "мм", '
            '"confidence": "high", "source_quote": "DN 100"}\n```'
        )

    monkeypatch.setattr(LLMClient, "complete", fake_complete)

    result = await extract_attribute_baseline("Задвижка DN 100.", "DN")

    assert result == ExtractedValue(
        value="100",
        unit="мм",
        confidence="high",
        source_quote="DN 100",
    )


@pytest.mark.asyncio
async def test_baseline_keeps_permissive_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_complete(_self: LLMClient, system: str, user: str) -> str:
        return '{"value":"100","unit":"мм","confidence":"certain","source_quote":"DN 100"}'

    monkeypatch.setattr(LLMClient, "complete", fake_complete)

    result = await extract_attribute_baseline("Задвижка DN 100.", "DN")

    assert result.confidence == "certain"
