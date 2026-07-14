"""Acceptance-тесты фильтра подтверждающей цитаты."""

import pytest

from app.models import LLMExtractionResponse
from app.modules.grounding import ground_response
from app.modules.registry import get_attribute


def response(
    value: str | None,
    source_quote: str | None,
    *,
    unit: str | None = "мм",
) -> LLMExtractionResponse:
    """Собрать валидный ответ модели для сценария grounding."""
    if value is None:
        return LLMExtractionResponse(
            value=None,
            unit=None,
            confidence="low",
            source_quote=None,
        )
    return LLMExtractionResponse(
        value=value,
        unit=unit,
        confidence="high",
        source_quote=source_quote,
    )


def test_accepts_value_with_exact_supporting_quote() -> None:
    result = ground_response(
        response("100", "DN 100"),
        "Задвижка DN 100, корпус стальной.",
        get_attribute("DN"),
    )

    assert result.value == "100"
    assert result.rejected_reason is None


@pytest.mark.parametrize("source_quote", ["dn 100", "значение из справочника"])
def test_rejects_quote_absent_from_source(source_quote: str) -> None:
    result = ground_response(
        response("100", source_quote),
        "Задвижка DN 100, корпус стальной.",
        get_attribute("DN"),
    )

    assert result.value is None
    assert result.rejected_reason == "source_quote_not_found"
    assert result.source_quote == source_quote


def test_rejects_value_not_supported_by_existing_quote() -> None:
    result = ground_response(
        response("100", "длина 230 мм"),
        "Задвижка DN 100, строительная длина 230 мм.",
        get_attribute("DN"),
    )

    assert result.value is None
    assert result.rejected_reason == "value_not_supported_by_quote"


def test_rejects_missing_source_quote_with_specific_reason() -> None:
    result = ground_response(
        response("100", None),
        "Задвижка DN 100.",
        get_attribute("DN"),
    )

    assert result.value is None
    assert result.rejected_reason == "missing_source_quote"


def test_accepts_ocr_value_supported_by_exact_quote() -> None:
    result = ground_response(
        response("200", "D N 2 0 0"),
        "Затвор D N 2 0 0 (OCR-артефакт).",
        get_attribute("DN"),
    )

    assert result.value == "200"


def test_null_value_is_valid_abstention() -> None:
    result = ground_response(
        response(None, None, unit=None),
        "Данные о давлении отсутствуют.",
        get_attribute("PN"),
    )

    assert result.value is None
    assert result.confidence == "low"
    assert result.rejected_reason is None
