"""Проверки строгих Pydantic-контрактов извлечения."""

import pytest
from pydantic import ValidationError

from app.models import LLMExtractionResponse


def test_llm_response_accepts_required_nullable_fields() -> None:
    response = LLMExtractionResponse.model_validate_json(
        '{"value":null,"unit":null,"confidence":"low","source_quote":null}'
    )

    assert response.value is None
    assert response.confidence == "low"


@pytest.mark.parametrize(
    "payload",
    [
        '{"value":"100","unit":"мм","confidence":"certain","source_quote":"DN 100"}',
        '{"value":100,"unit":"мм","confidence":"high","source_quote":"DN 100"}',
        '{"value":"100","unit":"мм","confidence":"high"}',
        (
            '{"value":"100","unit":"мм","confidence":"high",'
            '"source_quote":"DN 100","explanation":"из текста"}'
        ),
        '{"value":" ","unit":"мм","confidence":"high","source_quote":"DN 100"}',
        '{"value":"100","unit":"мм","confidence":"high","source_quote":""}',
        '{"value":"100","unit":"мм","confidence":"high","source_quote":null}',
        '{"value":null,"unit":"мм","confidence":"high","source_quote":"DN 100"}',
    ],
)
def test_llm_response_rejects_schema_violations(payload: str) -> None:
    with pytest.raises(ValidationError):
        LLMExtractionResponse.model_validate_json(payload)
